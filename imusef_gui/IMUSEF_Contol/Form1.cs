using Newtonsoft.Json;
using Renci.SshNet;
using System;
using System.Collections.Generic;
using System.Drawing;
using System.IO;
using System.Net;
using System.Net.NetworkInformation;
using System.Net.Sockets;
using System.Text;
using System.Threading;
using System.Windows.Forms;
using Microsoft.VisualBasic;
using System.Globalization;

namespace IMUSEF_Control
{
    public partial class Form1 : Form
    {
        public delegate void delUpdateConnectionState(int state);
        public delegate void delUpdatePing(bool ping);
        public delegate void delUpdateStimConfig(IMUSEF_StimConfig stimConfig);
        public delegate void delUpdateSettings(String controller);
        public delegate void delHandleMessage(String message);
        public delegate void delUpdateFileName_Record(String FileName);        
        public delegate void delUpdateControllerConfig(IMUSEF_Config imusefConfig);
        public delegate void delUpdateUDP_DataValue(MyDataPoint udp_DataValue);
        public delegate void delUpdateIndicatorsAndStates(UDP_Data data);

        // Constants
        // Commands to IMUSEF
        public const string CMD_GET_STIM_PARAMS = "CMD_GET_STIM_PARAMS";
        public const string CMD_SET_STIM_PARAMS = "CMD_SET_STIM_PARAMS";

        public const string CMD_GET_SETTINGS = "CMD_GET_SETTINGS";
        public const string CMD_SET_SETTINGS = "CMD_SET_SETTINGS";

        public const string CMD_GET_CONTROLLER_PARAMS = "CMD_GET_CONTROLLER_PARAMS";
        public const string CMD_SET_CONTROLLER_PARAMS = "CMD_SET_CONTROLLER_PARAMS";
        
        public const string CMD_SET_TEST_STIMULATION = "CMD_SET_TEST_STIMULATION";
        public const string CMD_SET_STIMULATION_INTENSITY = "CMD_SET_STIMULATION_INTENSITY";

        public const string CMD_CALIBRATE_SYSTEM = "CMD_CALIBRATE_SYSTEM";
        public const string CMD_STOP_SYSTEM = "CMD_STOP_SYSTEM";

        public const string CMD_START_RECORD = "CMD_START_RECORD";
        public const string CMD_STOP_RECORD = "CMD_STOP_RECORD";

        public const string CMD_ADD_COMMENT = "CMD_ADD_COMMENT";

        public const string CMD_RESET_CYCLING_COMPUTER = "CMD_RESET_CYCLING_COMPUTER";

        public const string CMD_BIODEX_CHANGE_SIDE = "CMD_BIODEX_CHANGE_SIDE";
        public const string CMD_BIODEX_CALIBRATE_KNEEANGLE = "CMD_BIODEX_CALIBRATE_KNEEANGLE";

        // Responses from IMUSEF
        public const string CMD_RE_GET_STIM_PARAMS = "CMD_RE_GET_STIM_PARAMS";
        public const string CMD_RE_SET_STIM_PARAMS = "CMD_RE_SET_STIM_PARAMS";


        public const string CMD_RE_SETTINGS = "CMD_RE_SETTINGS";
        public const string CMD_RE_CONTROLLER_PARAMS = "CMD_RE_CONTROLLER_PARAMS";

        public const string CMD_RE_START_RECORD = "CMD_RE_START_RECORD";
        public const string CMD_RE_STOP_RECORD = "CMD_RE_STOP_RECORD";

        // SSH Connection Variables
        public const string SSH_IP = "192.168.4.1";
        public const string SSH_User = "pi";
        public const string SSH_Password = "berrylirmm";
        Thread startIMUSEFTHREAD;
        SshClient sshclient = new SshClient(SSH_IP, SSH_User, SSH_Password);

        // Rear Wheels
        public int WHEEL_CAT_TRIKE = 2099;
        public int WHEEL_ICE_TRIKE_BIG = 2007;
        public int WHEEL_ICE_TRIKE_SMALL = 1527;

        // Status Variables
        public int Status_Stimulator = -1;               
        public int Status_CrankAngle_Sensor = -1;
        public int Status_CrankAngle_Sensor_IMU = -1;
        public int Status_IMUs = -1;
        public int Status_HomeTrainer = -1;
        public int Status_PowerMeter = -1;        
        public int Status_HeartRateMonitor = -1;
        public int Status_DataLogging = -1;

        // Buttons
        public int Button_Emergency    = -1;
        public int Button_Left         = -1;
        public int Button_Right        = -1;
        public int Switch_Man_Auto  = -1;
        public int Button_Boost        = -1;



        public bool[] ActiveChannels = new bool[] {false, false, false, false, false, false, false, false};

        // Configuration
        IMUSEF_Config imusef_config = new IMUSEF_Config();
        String FilePath = "";

        // LockObject
        private Object lockObject = new Object();

        // Drawing
        private Thread drawThread;
        private int SleepTime_ChartWorker = 10;      //ms
        public Queue<MyDataPoint> dataQueue = new Queue<MyDataPoint>();
        public Point dataPoint1;
        public Point dataPoint2;

        // Ping
        public bool PING = false;
        private Thread pingThread;

        // Graph Settings
        Color color_Y1 = Color.Gold;
        Color color_Y2 = Color.SkyBlue;
        public double X_MIN = 0;
        public double X_MAX = 5; // [s]
        public double Y1_MIN = 0;
        public double Y1_MAX = 360;
        public double Y2_MIN = 0;
        public double Y2_MAX = 360;
        string Y1_Unit = "°";
        string Y2_Unit = "°";

        int idx_Y1 = 0;
        int idx_Y2 = 0;

        private bool kill_Threads = false;

        Double startTicks = -1;
        
        public int UDP_Receive_Port = 12345;        // Receiving Data from Server

                       
        UdpClient udpClient;
        myTCP_Client tcpClient;
        Thread UDP_Receive_Thread;

        JsonSerializerSettings jsonsettings;

        


        public Form1()
        {
            InitializeComponent();


        }

        private void Form1_Load(object sender, EventArgs e)
        {
            // Initialize JSON Settings
            jsonsettings = new JsonSerializerSettings();
            jsonsettings.TypeNameHandling = TypeNameHandling.Objects;
            jsonsettings.DefaultValueHandling = DefaultValueHandling.IgnoreAndPopulate;

            tcpClient = new myTCP_Client("192.168.4.1", 12346);
            tcpClient.ReceiveEvent += new myTCP_Client.ReceivedMessage(this.delegated_handleMessage);
            tcpClient.UpdatedStateEvent += new myTCP_Client.UpdatedState(this.updateConnectionState);
            tcpClient.start();

            connectUDPServer();

            CMB_Controller.SelectedIndex = 0;
            RB_Control_CrankAngle_CheckedChanged(sender, e);
         
            tabControl1.SelectTab(0);

            // Selections Drawing
            CB_Y1.SelectedIndex = 0;
            CB_Y2.SelectedIndex = 0;

            pingThread = new Thread(new ThreadStart(PingRaspberryWorker));
            pingThread.Start();


            updateZeroLine_Y1();
        }


        public void PingRaspberryWorker()
        {
            while (!kill_Threads)
            {

                try
                {
                    PING = ping(SSH_IP);
                    delegatedUpdatePing(PING);

                    Thread.Sleep(200);
                }
                catch (Exception ex)
                {
                    // Ignore
                }
          }
        }

        public void delegated_handleMessage(String _msg)
        {
            delHandleMessage DelMSG = new delHandleMessage(_handleMessage);
            this.TB_F.BeginInvoke(DelMSG, _msg);
        }

        /// <summary>
        /// Handles a TCP-Message received from IMUSEF
        /// </summary>
        /// <param name="msg"></param>
        private void _handleMessage(String msg)
        {
            if (msg.Equals("")) { return; }

            String[] data = msg.Split('@');

            if(data.Length <2)
            {
                Console.WriteLine("Unknown Message: " + msg);
                return;
            }

            String CMD = data[0];
            String DATA = data[1];

            // Received Stimparams
            if (CMD.Equals(CMD_RE_GET_STIM_PARAMS))
            {
                IMUSEF_StimConfig _config = JsonConvert.DeserializeObject<IMUSEF_StimConfig>(DATA);

                delegated_updateStimConfig(_config);
            }
            else if (CMD.Equals(CMD_RE_SET_STIM_PARAMS))
            {
                
                if (DATA.Equals("True"))
                {
                    MessageBox.Show("Update of parameters successful!", "Update StimParams", MessageBoxButtons.OK, MessageBoxIcon.Information);
                    
                }
                else
                {
                    MessageBox.Show("Parameter transferred to IMUSEF! Configuration of Stimulator FAILED.", "Update StimParams", MessageBoxButtons.OK, MessageBoxIcon.Error);
                }

                BT_load_config_from_IMUSEF.Enabled = true;
                BT_Update_IMUSEF.Enabled = true;
                BT_TestStim.Text = "TestStim ON";

                if (CMB_Controller.SelectedIndex==0 & Status_Stimulator == 1)
                {
                    BT_TestStim.Enabled = true;
                    BT_TestBurst.Enabled = true;
                }
            }
            else if (CMD.Equals(CMD_RE_SETTINGS))
            {
                delegated_updateSettings(DATA);
            }
            else if (CMD.Equals(CMD_RE_CONTROLLER_PARAMS))
            {
               IMUSEF_Config _config = JsonConvert.DeserializeObject<IMUSEF_Config>(DATA);
                delegated_updateControllerConfig(_config);
           
            }
            else if (CMD.Equals(CMD_RE_START_RECORD))
            {
                delegated_updateFileName_Record(DATA);
                

            }
            else if (CMD.Equals(CMD_RE_STOP_RECORD))
            {
                delegated_updateFileName_Record(DATA);

                
            }

            Console.WriteLine("Received" + msg);
        }


        public void delegatedUpdatePing(bool ping)
        {
            delUpdatePing DelUpdate = new delUpdatePing(updatePing);
            this.PB_Ping.BeginInvoke(DelUpdate, ping);
        }

        public void updatePing(bool ping)
        {
            if (ping)
            {
                PB_Ping.BackColor = Color.Lime;
            }
            else
            {
                PB_Ping.BackColor = Color.Red;
            }
        }


        public void updateConnectionState(int state)
        {
            delUpdateConnectionState DelUpdate = new delUpdateConnectionState(updateState);
            this.LBL_IMUSEF_Status.BeginInvoke(DelUpdate, state);
        }

        public void updateState(int state) { 

            if (state == myTCP_Client.NOT_CONNECTED)
            {

              LBL_IMUSEF_Status.Text = "Not connected";
              Connection_Bar.Value = 0;

              activateTCPControllerElements();

            }
            else if (state == myTCP_Client.CONNECTING)
            {
                LBL_IMUSEF_Status.Text = "Searching for IMUSEF";

                int val = Connection_Bar.Value;
                val = val + 10;

                if (val > 90) { val = 10; }

                Connection_Bar.Value = val;
                
                BT_load_config_from_IMUSEF.Enabled = false;
                BT_Update_IMUSEF.Enabled = false;
                BT_Load_ControllerConfig.Enabled = false;
                BT_Update_ControllerConfig.Enabled = false;
                
                CMB_Controller.Enabled = false;

                CB_Simulate_CrankAngle.Enabled = false;
                CB_Simulate_KneeAngles.Enabled = false;
                CB_Simulate_ThighAngles.Enabled = false;
                TB_Simulation_RPM.Enabled = false;
                BT_UpdateCadence.Enabled = false;

                CB_Activate_Button_Emergency.Enabled = false;
                CB_Activate_Button_Left.Enabled = false;
                CB_Activate_Button_Right.Enabled = false;
                CB_Activate_Button_Boost.Enabled = false;
                CB_Activate_Switch_Man_Auto.Enabled = false;

                CB_Module_Relaybox.Enabled = false;
                CB_Module_Stimulator.Enabled = false;
                CB_Module_CrankSensor_OpenDAQ.Enabled = false;
                CB_Module_CrankSensor_IMU_Fox.Enabled = false;
                CB_Module_IMUs.Enabled = false;
                CB_Module_Heartrate_Monitor.Enabled = false;
                CB_Module_PowerMeter_Rotor.Enabled = false;
                CB_Module_HomeTrainer.Enabled = false;

                TB_Max_Manual_Cadence.Enabled = false;
                TB_MAC_Stimulator.Enabled = false;
                TB_ID_ROTOR.Enabled = false;
                TB_ID_HeartRateMonitor.Enabled = false;
                CMB_RearWheel.Enabled = false;
                BT_Update_Max_Manual_Cadence.Enabled = false;

                BT_Calibrate.Enabled = false;
                BT_Start_IMUSEF.Enabled = true;
                BT_Stop_IMUSEF.Enabled = false;
                BT_Restart_Imusef2.Enabled = false;

                PB_LED_IMU_Ready.BackColor = Color.Silver;
                PB_Status_CrankSensor.BackColor = Color.Silver;
                PB_LED_CrankSensor_IMU.BackColor = Color.Silver;
                PB_LED_Stimulator.BackColor = Color.Silver;
                PB_LED_EmergencyButton.BackColor = Color.Silver;
                LBL_Button_Emergency.Text = "Emergency Button";
                PB_LED_PowerMeter.BackColor = Color.Silver;
                PB_LED_HomeTrainer.BackColor = Color.Silver;
                PB_LED_HeartRate_Monitor.BackColor = Color.Silver;
                PB_DataLogging.BackColor = Color.Silver;

                LBL_Status_IMUs.Enabled = false;
                LBL_Status_IMU_Fox.Enabled = false;
                LBL_Status_Stimulator.Enabled = false;
                LBL_Button_Emergency.Enabled = false;
                LBL_Button_Left.Enabled = false;
                LBL_Button_Right.Enabled = false;
                LBL_Button_Boost.Enabled = false;
                LBL_Switch_Man_Auto.Enabled = false;
                LBL_Status_CrankAngleSensor.Enabled = false;
                GB_ROTOR_Powermeter.Enabled = false;
                GB_Status_Hometrainer.Enabled = false;
                LBL_Status_HeartrateMonitor.Enabled = false;

                BT_StartStop_Logging.Enabled = false;

                Status_IMUs = -1;
                Status_CrankAngle_Sensor = -1;
                Status_CrankAngle_Sensor_IMU = -1;
                Status_Stimulator = -1;               
                Status_PowerMeter = -1;
                Status_HomeTrainer = -1;
                Status_HeartRateMonitor = -1;

                Button_Emergency = -1;
                Button_Left = -1;
                Button_Right = -1;
                Button_Boost = -1;
                Switch_Man_Auto = -1;


                activateTCPControllerElements();
            }
            else if (state == myTCP_Client.CONNECTED)
            {

                LBL_IMUSEF_Status.Text = "Connected to IMUSEF";
                Connection_Bar.Value = 100;

                BT_load_config_from_IMUSEF.Enabled = true;
                BT_Update_IMUSEF.Enabled = true;
                BT_Load_ControllerConfig.Enabled = true;
                BT_Update_ControllerConfig.Enabled = true;

                BT_Calibrate.Enabled = true;
                BT_Start_IMUSEF.Enabled = false;
                BT_Stop_IMUSEF.Enabled = true;
                BT_Restart_Imusef2.Enabled = true;

                BT_StartStop_Logging.Enabled = true;


                activateTCPControllerElements();

                // Ask which controller mode is currently active
                tcpClient.sendMessage(CMD_GET_SETTINGS + "@");
            }
        }

        public void delegated_updateStimConfig(IMUSEF_StimConfig _params)
        {
            delUpdateStimConfig DelUpdate = new delUpdateStimConfig(updateStimConfig);
            this.TB_F.BeginInvoke(DelUpdate, _params);
        }

        public void updateStimConfig(IMUSEF_StimConfig _params)
        {
            TB_F.Text = _params.F.ToString();
            TB_F_BOOST.Text = _params.F_Boost.ToString();

            CB_MonoPh_1.Checked = _params.Monophasic[0];
            CB_MonoPh_2.Checked = _params.Monophasic[1];
            CB_MonoPh_3.Checked = _params.Monophasic[2];
            CB_MonoPh_4.Checked = _params.Monophasic[3];
            CB_MonoPh_5.Checked = _params.Monophasic[4];
            CB_MonoPh_6.Checked = _params.Monophasic[5];
            CB_MonoPh_7.Checked = _params.Monophasic[6];
            CB_MonoPh_8.Checked = _params.Monophasic[7];

            TB_PhW1.Text = _params.PhW[0].ToString();
            TB_PhW2.Text = _params.PhW[1].ToString();
            TB_PhW3.Text = _params.PhW[2].ToString();
            TB_PhW4.Text = _params.PhW[3].ToString();
            TB_PhW5.Text = _params.PhW[4].ToString();
            TB_PhW6.Text = _params.PhW[5].ToString();
            TB_PhW7.Text = _params.PhW[6].ToString();
            TB_PhW8.Text = _params.PhW[7].ToString();

            TB_PhW1_BOOST.Text = _params.PhW_Boost[0].ToString();
            TB_PhW2_BOOST.Text = _params.PhW_Boost[1].ToString();
            TB_PhW3_BOOST.Text = _params.PhW_Boost[2].ToString();
            TB_PhW4_BOOST.Text = _params.PhW_Boost[3].ToString();
            TB_PhW5_BOOST.Text = _params.PhW_Boost[4].ToString();
            TB_PhW6_BOOST.Text = _params.PhW_Boost[5].ToString();
            TB_PhW7_BOOST.Text = _params.PhW_Boost[6].ToString();
            TB_PhW8_BOOST.Text = _params.PhW_Boost[7].ToString();

            TB_IPG1.Text = _params.IPG[0].ToString();
            TB_IPG2.Text = _params.IPG[1].ToString();
            TB_IPG3.Text = _params.IPG[2].ToString();
            TB_IPG4.Text = _params.IPG[3].ToString();
            TB_IPG5.Text = _params.IPG[4].ToString();
            TB_IPG6.Text = _params.IPG[5].ToString();
            TB_IPG7.Text = _params.IPG[6].ToString();
            TB_IPG8.Text = _params.IPG[7].ToString();

            TB_Imax1.Text = _params.I_Max[0].ToString();
            TB_Imax2.Text = _params.I_Max[1].ToString();
            TB_Imax3.Text = _params.I_Max[2].ToString();
            TB_Imax4.Text = _params.I_Max[3].ToString();
            TB_Imax5.Text = _params.I_Max[4].ToString();
            TB_Imax6.Text = _params.I_Max[5].ToString();
            TB_Imax7.Text = _params.I_Max[6].ToString();
            TB_Imax8.Text = _params.I_Max[7].ToString();

            TB_Ramp_UP1.Text = _params.RampUP[0].ToString();
            TB_Ramp_UP2.Text = _params.RampUP[1].ToString();
            TB_Ramp_UP3.Text = _params.RampUP[2].ToString();
            TB_Ramp_UP4.Text = _params.RampUP[3].ToString();
            TB_Ramp_UP5.Text = _params.RampUP[4].ToString();
            TB_Ramp_UP6.Text = _params.RampUP[5].ToString();
            TB_Ramp_UP7.Text = _params.RampUP[6].ToString();
            TB_Ramp_UP8.Text = _params.RampUP[7].ToString();

            TB_Ramp_DOWN1.Text = _params.RampDOWN[0].ToString();
            TB_Ramp_DOWN2.Text = _params.RampDOWN[1].ToString();
            TB_Ramp_DOWN3.Text = _params.RampDOWN[2].ToString();
            TB_Ramp_DOWN4.Text = _params.RampDOWN[3].ToString();
            TB_Ramp_DOWN5.Text = _params.RampDOWN[4].ToString();
            TB_Ramp_DOWN6.Text = _params.RampDOWN[5].ToString();
            TB_Ramp_DOWN7.Text = _params.RampDOWN[6].ToString();
            TB_Ramp_DOWN8.Text = _params.RampDOWN[7].ToString();
        }

        public void delegated_updateSettings(String _settings)
        {
            delUpdateSettings DelUpdate = new delUpdateSettings(updateSettings);
            this.TB_F.BeginInvoke(DelUpdate, _settings);
        }

        public void updateSettings(String _settings)
        {

            TCP_Message_Settings msg = JsonConvert.DeserializeObject<TCP_Message_Settings>(_settings);

            // Select the active Controller
            if (msg.Controller.Equals(IMUSEF_ControllerConfig.CONTROLLER_TCP))
            {
                CMB_Controller.SelectedIndex = 0;
            }
            else if (msg.Controller.Equals(IMUSEF_ControllerConfig.CONTROLLER_CRANKANGLE))
            {
                CMB_Controller.SelectedIndex = 1;
            }
            else if (msg.Controller.Equals(IMUSEF_ControllerConfig.CONTROLLER_THIGHANGLE))
            {
                CMB_Controller.SelectedIndex = 2;
            }
            else if (msg.Controller.Equals(IMUSEF_ControllerConfig.CONTROLLER_KNEEANGLE))
            {
                CMB_Controller.SelectedIndex = 3;
            }            
            else if (msg.Controller.Equals(IMUSEF_ControllerConfig.CONTROLLER_OBSERVER))
            {
                CMB_Controller.SelectedIndex = 4;
            }
            else if (msg.Controller.Equals(IMUSEF_ControllerConfig.CONTROLLER_BIODEX))
            {
                CMB_Controller.SelectedIndex = 5;
            }
            else
            {
                MessageBox.Show("There is no Controller: <" + msg.Controller + ">. Sorry!");
                CMB_Controller.SelectedIndex = -1;
            }

            // Simulation
            CB_Simulate_CrankAngle.Checked = msg.Simulate_CrankAngle;
            CB_Simulate_KneeAngles.Checked = msg.Simulate_KneeAngles;
            CB_Simulate_ThighAngles.Checked = msg.Simulate_ThighAngles;
            TB_Simulation_RPM.Text = msg.Simulated_Cadence.ToString();

            // Button CheckBoxes
            CB_Activate_Button_Emergency.Checked = msg.FLAG_Button_Emergency;
            CB_Activate_Button_Left.Checked = msg.FLAG_Button_Left;
            CB_Activate_Button_Right.Checked = msg.FLAG_Button_Right;
            CB_Activate_Button_Boost.Checked = msg.FLAG_Button_Boost;
            CB_Activate_Switch_Man_Auto.Checked = msg.FLAG_Switch_Man_Auto;

            // Module CheckBoxes
            CB_Module_Relaybox.Checked = msg.FLAG_Module_RelayBox;
            CB_Module_Stimulator.Checked = msg.FLAG_Module_Stimulator;
            CB_Module_CrankSensor_OpenDAQ.Checked = msg.FLAG_Module_CrankAngle_Sensor_OpenDAQ;
            CB_Module_CrankSensor_IMU_Fox.Checked = msg.FLAG_Module_CrankAngle_Sensor_IMU_FOX;
            CB_Module_IMUs.Checked = msg.FLAG_Module_IMUs;
            CB_Module_Heartrate_Monitor.Checked = msg.FLAG_Module_Heartrate_Monitor;
            CB_Module_PowerMeter_Rotor.Checked = msg.FLAG_Module_PowerMeter_Rotor;
            CB_Module_HomeTrainer.Checked = msg.FLAG_Module_HomeTrainer;

            // General Settings
            TB_Max_Manual_Cadence.Text = msg.Max_Manual_Cadence.ToString();
            TB_MAC_Stimulator.Text = msg.MAC_Stimulator;
            TB_ID_ROTOR.Text = msg.ID_ROTOR.ToString();
            TB_ID_HeartRateMonitor.Text = msg.ID_HeartRateMonitor.ToString();

            if (msg.WheelCircumference == WHEEL_CAT_TRIKE)
            {
                CMB_RearWheel.SelectedIndex = 0;
            }
            else if (msg.WheelCircumference == WHEEL_ICE_TRIKE_BIG)
            {
                CMB_RearWheel.SelectedIndex = 1;
            }
            else if (msg.WheelCircumference == WHEEL_ICE_TRIKE_SMALL)
            {
                CMB_RearWheel.SelectedIndex = 0;
            }
            else
            {
                CMB_RearWheel.SelectedIndex = -1;
            }


            // Enable Control Elements

            CMB_Controller.Enabled = true;

            CB_Simulate_CrankAngle.Enabled = true;
            CB_Simulate_KneeAngles.Enabled = true;
            CB_Simulate_ThighAngles.Enabled = true;
            TB_Simulation_RPM.Enabled = true;
            BT_UpdateCadence.Enabled = true;

            CB_Activate_Button_Emergency.Enabled = true;
            CB_Activate_Button_Left.Enabled = true;
            CB_Activate_Button_Right.Enabled = true;
            CB_Activate_Button_Boost.Enabled = true;
            CB_Activate_Switch_Man_Auto.Enabled = true;

            CB_Module_Relaybox.Enabled = true;
            CB_Module_Stimulator.Enabled = true;
            CB_Module_CrankSensor_OpenDAQ.Enabled = true;
            CB_Module_CrankSensor_IMU_Fox.Enabled = true;
            CB_Module_IMUs.Enabled = true;
            CB_Module_Heartrate_Monitor.Enabled = true;
            CB_Module_PowerMeter_Rotor.Enabled = true;
            CB_Module_HomeTrainer.Enabled = true;

            TB_Max_Manual_Cadence.Enabled = true;
            TB_MAC_Stimulator.Enabled = true;
            TB_ID_ROTOR.Enabled = true;
            TB_ID_HeartRateMonitor.Enabled = true;
            CMB_RearWheel.Enabled = true;
            BT_Update_Max_Manual_Cadence.Enabled = true;

            // Update Datalogging Elements
            if (msg.DataLogging_Active)
            {
                BT_StartStop_Logging.Text = "Start";  // Needs to get from Start -> Stop 
            }
            else
            {
                BT_StartStop_Logging.Text = "Stop"; // Needs to get from Stop -> Start
            }

            updateFileName_Record(msg.DataLogging_FilePath);

            activateTCPControllerElements();

        }

        public void delegated_updateFileName_Record(String _filename_record)
        {
            delUpdateFileName_Record DelUpdate = new delUpdateFileName_Record(updateFileName_Record);
            this.TB_Filename_Recording.BeginInvoke(DelUpdate, _filename_record);
        }

        public void updateFileName_Record(String _filename_record)
        {
                

            // Recording has been started
            if (BT_StartStop_Logging.Text.Equals("Start"))
            {
                LBL_RecordingFile.Text = "Path to File:";

                TB_Filename_Recording.Text = _filename_record;
                BT_StartStop_Logging.Text = "Stop";
                TB_Filename_Recording.Enabled = false;
                BT_StartStop_Logging.Enabled = true;
                TB_Comment.Enabled = true;
                BT_Add_Comment.Enabled = true;
            }

            // Recording has been stopped
            else
            {
                LBL_RecordingFile.Text = "File Name:";

                string Filename = _filename_record.Replace("Data/", "");

                string Directory = "";

                

                string[] splits = Filename.Split('/');

                if (splits.Length == 1)
                {
                    Filename = splits[0];
                }
                else if (splits.Length == 2)
                {
                    Directory = splits[0];
                    Filename = splits[1];
                }
                                               
                try
                {
                    // Check if Filename has an initial Numbering and _ like "0001_"; if remove
                    string str_number = Filename.Substring(0, 4);

                    Int32 number = Int32.Parse(str_number);

                    if (Filename[4].Equals('_'))
                    {
                        Filename = Filename.Remove(0, 5);
                    }
                }
                catch (Exception e)
                {
                }

                BT_StartStop_Logging.Text = "Start";
                TB_Filename_Recording.Enabled = true;
                BT_StartStop_Logging.Enabled = true;
                TB_Comment.Enabled = false;
                BT_Add_Comment.Enabled = false;

                if (Directory.Equals(""))
                {
                    TB_Filename_Recording.Text = Filename;
                }
                else
                {
                    TB_Filename_Recording.Text = Directory + "/" + Filename;
                }

                if (!Filename.Equals(""))
                {
                    MessageBox.Show("Recording successfully saved: " + _filename_record);
                }                         

            }
            
        }


        public void delegated_updateControllerConfig(IMUSEF_Config _config)
        {
            delUpdateControllerConfig DelUpdate = new delUpdateControllerConfig(updateControllerConfig);
            this.TB_F.BeginInvoke(DelUpdate, _config);
        }

        public void updateControllerConfig(IMUSEF_Config _config)
        {
            imusef_config.CrankAngle_ControllerConfig = _config.CrankAngle_ControllerConfig;
            imusef_config.KneeAngle_ControllerConfig = _config.KneeAngle_ControllerConfig;
            imusef_config.ThighAngle_ControllerConfig = _config.ThighAngle_ControllerConfig;
            imusef_config.Observer_ControllerConfig = _config.Observer_ControllerConfig;
            imusef_config.Biodex_ControllerConfig = _config.Biodex_ControllerConfig;

            RB_Control_CrankAngle_CheckedChanged(this, new EventArgs());
        }


        public void delegated_updateUDP_DataValue(MyDataPoint point)
        {
            delUpdateUDP_DataValue DelUpdate = new delUpdateUDP_DataValue(updateUDP_DataValues);
            this.TB_F.BeginInvoke(DelUpdate, point);
        }

        public void updateUDP_DataValues(MyDataPoint point)
        {
            if (idx_Y1 > 0)
            {
                LBL_Value_Y1.Text = Math.Round(point.Y1, 1) + Y1_Unit;
            }
            else
            {
                LBL_Value_Y1.Text = "-";
            }

            if (idx_Y2 > 0)
            {
                LBL_Value_Y2.Text = Math.Round(point.Y2, 1) + Y2_Unit;
            }
            else
            {
                LBL_Value_Y2.Text = "-";
            }

        }

        
        public void delegated_updateIndicatorsAndSystemStates(UDP_Data _data)
        {
            delUpdateIndicatorsAndStates DelUpdate = new delUpdateIndicatorsAndStates(updateIndicatorsAndSystemStates);
            this.PB_Indicator_LEFT.BeginInvoke(DelUpdate, _data);
        }



        public void updateIndicatorsAndSystemStates(UDP_Data _data)
        {

            double Y_ind_left = 0;
            double Y_ind_right = 0;

            
            if (RB_Control_CrankAngle.Checked)
            {
                Y_ind_left = _data.CrankAngle_OpenDAQ;
                Y_ind_right = _data.CrankAngle_OpenDAQ;
            }
            else if (RB_Control_ThighAngle.Checked)
            {
                Y_ind_left = _data.LeftThighAngle_normalized;
                Y_ind_right = _data.RightThighAngle_normalized;
            }
            else if (RB_Control_KneeAngle.Checked)
            {
                Y_ind_left = _data.LeftKneeAngle_normalized;
                Y_ind_right = _data.RightKneeAngle_normalized;
            }
            else if (RB_Control_Observer.Checked)
            {
                Y_ind_left = _data.ObserverPhase;
                Y_ind_right = _data.ObserverPhase;
            }
            else if (RB_Control_Biodex.Checked)
            {
                Y_ind_left = _data.DebugValue;
                Y_ind_right = _data.DebugValue;
            }

            // Cycling Computer
            LBL_CyclingComputer_Cadence.Text = _data.Cadence_CyclingComputer.ToString("0", CultureInfo.InvariantCulture);
            LBL_CyclingComputer_Speed.Text = _data.Speed_CyclingComputer.ToString("0.0", CultureInfo.InvariantCulture);
            LBL_CyclingComputer_Distance.Text = _data.Distance_CyclingComputer.ToString("0", CultureInfo.InvariantCulture);

            // Hometrainer
            LBL_HomeTrainer_Power_AVG.Text = _data.Power_AVG_HomeTrainer.ToString("0.0", CultureInfo.InvariantCulture);
            LBL_HomeTrainer_Speed.Text = _data.Speed_HomeTrainer.ToString("0.0", CultureInfo.InvariantCulture);

            // Rotor Powermetwer
            LBL_Cadence_ROTOR.Text = Math.Round(_data.Cadence_PowerMeter, 0).ToString();
            LBL_Power_Total_ROTOR.Text = _data.Power_Total_PowerMeter.ToString("0.0", CultureInfo.InvariantCulture);
            LBL_Power_Left_ROTOR.Text = _data.Power_Left_PowerMeter.ToString("0.0", CultureInfo.InvariantCulture);
            LBL_Power_Right_ROTOR.Text = _data.Power_Right_PowerMeter.ToString("0.0", CultureInfo.InvariantCulture);

            // DataRate PowerMeter
            LBL_Status_PowerMeter.Text = "(" + (int)Math.Round(_data.DataRate_F1_PowerMeter) + "/" + (int)Math.Round(_data.DataRate_F2_PowerMeter) + "/" + (int)Math.Round(_data.DataRate_F3_PowerMeter) + ")";

            // Uptime
            TimeSpan t = TimeSpan.FromSeconds(_data.Timestamp);
            string formated_time = string.Format("{0:D2}h:{1:D2}m:{2:D2}s", t.Hours, t.Minutes, t.Seconds);
            LBL_Uptime.Text = formated_time;


            if (CB_ShowIndicators.Checked) {
                int startX1 = 116;
                int startX2 = 593;
                int startY = 21;

                int xxx = (int)((double)260 * ((double)Y_ind_left - (double)SL_START_CH1.Minimum) / ((double)SL_START_CH1.Maximum - (double)SL_START_CH1.Minimum));

                PB_Indicator_LEFT.Location = new Point(startX1 + xxx, startY);

                xxx = (int)((double)260 * ((double)Y_ind_right - (double)SL_START_CH1.Minimum) / ((double)SL_START_CH1.Maximum - (double)SL_START_CH1.Minimum));

                PB_Indicator_RIGHT.Location = new Point(startX2 + xxx, startY);
            }

            // Update Channel LEDs

            bool[] t_active_channels = new bool[] { false, false, false, false, false, false, false, false };

            if (RB_Control_CrankAngle.Checked)
            {
                t_active_channels = _data.CrankAngle_Controller_activeChannels;
            }
            else if (RB_Control_KneeAngle.Checked)
            {
                t_active_channels = _data.KneeAngle_Controller_activeChannels;
            }
            else if (RB_Control_ThighAngle.Checked)
            {
                t_active_channels = _data.ThighAngle_Controller_activeChannels;
            }
            else if (RB_Control_Observer.Checked)
            {
                t_active_channels = _data.Observer_Controller_activeChannels;
            }
            else if (RB_Control_Biodex.Checked)
            {
                t_active_channels = _data.Biodex_Controller_activeChannels;
            }

            if (ActiveChannels[0] != t_active_channels[0])
            {
                ActiveChannels[0] = t_active_channels[0];
                Color col = Color.Silver;

                if (ActiveChannels[0])
                {
                    col = Color.Lime;
                }

                PB_LED_CH1_active.BackColor = col;
            }


            if (ActiveChannels[1] != t_active_channels[1])
            {
                ActiveChannels[1] = t_active_channels[1];
                Color col = Color.Silver;

                if (ActiveChannels[1])
                {
                    col = Color.Lime;
                }

                PB_LED_CH2_active.BackColor = col;
            }

            if (ActiveChannels[2] != t_active_channels[2])
            {
                ActiveChannels[2] = t_active_channels[2];
                Color col = Color.Silver;

                if (ActiveChannels[2])
                {
                    col = Color.Lime;
                }

                PB_LED_CH3_active.BackColor = col;
            }

            if (ActiveChannels[3] != t_active_channels[3])
            {
                ActiveChannels[3] = t_active_channels[3];
                Color col = Color.Silver;

                if (ActiveChannels[3])
                {
                    col = Color.Lime;
                }

                PB_LED_CH4_active.BackColor = col;
            }

            if (ActiveChannels[4] != t_active_channels[4])
            {
                ActiveChannels[4] = t_active_channels[4];
                Color col = Color.Silver;

                if (ActiveChannels[4])
                {
                    col = Color.Lime;
                }

                PB_LED_CH5_active.BackColor = col;
            }

            if (ActiveChannels[5] != t_active_channels[5])
            {
                ActiveChannels[5] = t_active_channels[5];
                Color col = Color.Silver;

                if (ActiveChannels[5])
                {
                    col = Color.Lime;
                }

                PB_LED_CH6_active.BackColor = col;
            }

            if (ActiveChannels[6] != t_active_channels[6])
            {
                ActiveChannels[6] = t_active_channels[6];
                Color col = Color.Silver;

                if (ActiveChannels[6])
                {
                    col = Color.Lime;
                }

                PB_LED_CH7_active.BackColor = col;
            }

            if (ActiveChannels[7] != t_active_channels[7])
            {
                ActiveChannels[7] = t_active_channels[7];
                Color col = Color.Silver;

                if (ActiveChannels[7])
                {
                    col = Color.Lime;
                }

                PB_LED_CH8_active.BackColor = col;
            }




            // Update Statuses
            if (Status_Stimulator != _data.Status_Stimulator)
            {
                // Update
                Status_Stimulator = _data.Status_Stimulator;


                if (Status_Stimulator == -2)
                {
                    PB_LED_Stimulator.BackColor = Color.Red;
                    LBL_Status_Stimulator.Enabled = true;
                    BT_TestStim.Enabled = false;
                    BT_TestBurst.Enabled = false;
                }
                else if (Status_Stimulator == -1)
                {
                    PB_LED_Stimulator.BackColor = Color.Silver;
                    LBL_Status_Stimulator.Enabled = false;
                    BT_TestStim.Enabled = false;
                    BT_TestBurst.Enabled = false;
                }
                else if (Status_Stimulator == 0)
                {
                    PB_LED_Stimulator.BackColor = Color.Gold;
                    LBL_Status_Stimulator.Enabled = true;
                    BT_TestStim.Enabled = false;
                    BT_TestBurst.Enabled = false;
                }
                else if (Status_Stimulator == 1)
                {
                    PB_LED_Stimulator.BackColor = Color.Lime;
                    LBL_Status_Stimulator.Enabled = true;
                    if (CMB_Controller.SelectedIndex==0)
                    {
                        BT_TestStim.Enabled = true;
                        BT_TestBurst.Enabled = true;
                    }
                }
            }            


            // Update Emergency Button - regular update 
            if (Button_Emergency != _data.Button_Emergency)
            {
                // Update
                Button_Emergency = _data.Button_Emergency;


                if (Button_Emergency == 0)
                {
                    PB_LED_EmergencyButton.BackColor = Color.Lime;
                    LBL_Button_Emergency.Text = "Emergency Button: OK";
                    LBL_Button_Emergency.Enabled = true;

                }
                else if (Button_Emergency == 1)
                {
                    PB_LED_EmergencyButton.BackColor = Color.Red;
                    LBL_Button_Emergency.Text = "Emergency Button: PRESSED";
                    LBL_Button_Emergency.Enabled = true;
                }
                else
                {
                    PB_LED_EmergencyButton.BackColor = Color.Silver;
                    LBL_Button_Emergency.Text = "Emergency Button: DEACTIVATED";
                    LBL_Button_Emergency.Enabled = false;
                }
            }

            if (Button_Left != _data.Button_LEFT)
            {
                // Update
                Button_Left = _data.Button_LEFT;


                if (Button_Left == 1)
                {
                    PB_LED_Button_Left.BackColor = Color.Lime;
                    LBL_Button_Left.Enabled = true;

                }
                else if (Button_Left == 0)
                {
                    PB_LED_Button_Left.BackColor = Color.Silver;
                    LBL_Button_Left.Enabled = true;
                }
                else
                {
                    PB_LED_Button_Left.BackColor = Color.Silver;
                    LBL_Button_Left.Enabled = false;
                }
            }

            if (Button_Right != _data.Button_RIGHT)
            {
                // Update
                Button_Right = _data.Button_RIGHT;


                if (Button_Right == 1)
                {
                    PB_LED_Button_Right.BackColor = Color.Lime;
                    LBL_Button_Right.Enabled = true;

                }
                else if (Button_Right == 0)
                {
                    PB_LED_Button_Right.BackColor = Color.Silver;
                    LBL_Button_Right.Enabled = true;
                }
                else
                {
                    PB_LED_Button_Right.BackColor = Color.Silver;
                    LBL_Button_Right.Enabled = false;
                }
            }

            if (Button_Boost != _data.Button_BOOST)
            {
                // Update
                Button_Boost = _data.Button_BOOST;


                if (Button_Boost == 1)
                {
                    PB_LED_Button_Boost.BackColor = Color.Lime;
                    LBL_Button_Boost.Enabled = true;

                }
                else if (Button_Boost == 0)
                {
                    PB_LED_Button_Boost.BackColor = Color.Silver;
                    LBL_Button_Boost.Enabled = true;
                }
                else
                {
                    PB_LED_Button_Boost.BackColor = Color.Silver;
                    LBL_Button_Boost.Enabled = false;
                }
            }

            if (Switch_Man_Auto != _data.Switch_MAN_AUTO)
            {
                // Update
                Switch_Man_Auto = _data.Switch_MAN_AUTO;


                if (Switch_Man_Auto == 1)
                {
                    PB_LED_Switch_Man_Auto.BackColor = Color.Lime;
                    LBL_Switch_Man_Auto.Text = "Switch: AUTO";
                    LBL_Switch_Man_Auto.Enabled = true;

                }
                else if (Switch_Man_Auto == 0)
                {
                    PB_LED_Switch_Man_Auto.BackColor = Color.Silver;
                    LBL_Switch_Man_Auto.Text = "Switch: MANUAL";
                    LBL_Switch_Man_Auto.Enabled = true;
                }
                else
                {
                    PB_LED_Switch_Man_Auto.BackColor = Color.Silver;
                    LBL_Switch_Man_Auto.Text = "Switch: deactivated";
                    LBL_Switch_Man_Auto.Enabled = false;
                }
            }

            if (Status_CrankAngle_Sensor != _data.Status_CrankAngle_OpenDAQ)
            {
                // Update
                Status_CrankAngle_Sensor = _data.Status_CrankAngle_OpenDAQ;


                if (Status_CrankAngle_Sensor == -2)
                {
                    PB_Status_CrankSensor.BackColor = Color.Red;
                    LBL_Status_CrankAngleSensor.Enabled = true;
                }
                else if (Status_CrankAngle_Sensor == -1)
                {
                    PB_Status_CrankSensor.BackColor = Color.Silver;
                    LBL_Status_CrankAngleSensor.Enabled = false;
                }
                else if (Status_CrankAngle_Sensor == 0)
                {
                    PB_Status_CrankSensor.BackColor = Color.Gold;
                    LBL_Status_CrankAngleSensor.Enabled = true;
                }
                else if (Status_CrankAngle_Sensor == 1)
                {
                    PB_Status_CrankSensor.BackColor = Color.Lime;
                    LBL_Status_CrankAngleSensor.Enabled = true;
                }
            }

            if (Status_CrankAngle_Sensor_IMU != _data.Status_CrankAngle_IMU_FOX)
            {
                // Update
                Status_CrankAngle_Sensor_IMU = _data.Status_CrankAngle_IMU_FOX;


                if (Status_CrankAngle_Sensor_IMU == -2)
                {
                    PB_LED_CrankSensor_IMU.BackColor = Color.Red;
                    LBL_Status_IMU_Fox.Enabled = true;
                }
                else if (Status_CrankAngle_Sensor_IMU == -1)
                {
                    PB_LED_CrankSensor_IMU.BackColor = Color.Silver;
                    LBL_Status_IMU_Fox.Enabled = false;
                }
                else if (Status_CrankAngle_Sensor_IMU == 0)
                {
                    PB_LED_CrankSensor_IMU.BackColor = Color.Gold;
                    LBL_Status_IMU_Fox.Enabled = true;
                }
                else if (Status_CrankAngle_Sensor_IMU == 1)
                {
                    PB_LED_CrankSensor_IMU.BackColor = Color.Lime;
                    LBL_Status_IMU_Fox.Enabled = true;
                }
            }

            if (Status_IMUs != _data.Status_IMUs)
            {
                // Update
                Status_IMUs = _data.Status_IMUs;


                if (Status_IMUs == -2)
                {
                    PB_LED_IMU_Ready.BackColor = Color.Red;
                    LBL_Status_IMUs.Enabled = true;
                }
                else if (Status_IMUs == -1)
                {
                    PB_LED_IMU_Ready.BackColor = Color.Silver;
                    LBL_Status_IMUs.Enabled = false;
                }
                else if (Status_IMUs == 0)
                {
                    PB_LED_IMU_Ready.BackColor = Color.Gold;
                    LBL_Status_IMUs.Enabled = true;
                }
                else if (Status_IMUs == 1)
                {
                    PB_LED_IMU_Ready.BackColor = Color.Lime;
                    LBL_Status_IMUs.Enabled = true;
                }                
            }

            if (Status_HomeTrainer != _data.Status_HomeTrainer)
            {
                // Update
                Status_HomeTrainer = _data.Status_HomeTrainer;


                if (Status_HomeTrainer == -2)
                {
                    PB_LED_HomeTrainer.BackColor = Color.Red;
                    GB_Status_Hometrainer.Enabled = true;
                }
                else if (Status_HomeTrainer == -1)
                {
                    PB_LED_HomeTrainer.BackColor = Color.Silver;
                    GB_Status_Hometrainer.Enabled = false;
                }
                else if (Status_HomeTrainer == 0)
                {
                    PB_LED_HomeTrainer.BackColor = Color.Gold;
                    GB_Status_Hometrainer.Enabled = true;
                }
                else if (Status_HomeTrainer == 1)
                {
                    PB_LED_HomeTrainer.BackColor = Color.Lime;
                    GB_Status_Hometrainer.Enabled = true;
                }
            }

            if (Status_PowerMeter != _data.Status_PowerMeter)
            {
                // Update
                Status_PowerMeter = _data.Status_PowerMeter;


                if (Status_PowerMeter == -2)
                {
                    PB_LED_PowerMeter.BackColor = Color.Red;
                    GB_ROTOR_Powermeter.Enabled = true;
                }
                else if (Status_PowerMeter == -1)
                {
                    PB_LED_PowerMeter.BackColor = Color.Silver;
                    GB_ROTOR_Powermeter.Enabled = false;
                }
                else if (Status_PowerMeter == 0)
                {
                    PB_LED_PowerMeter.BackColor = Color.Gold;
                    GB_ROTOR_Powermeter.Enabled = true;
                }
                else if (Status_PowerMeter == 1)
                {
                    PB_LED_PowerMeter.BackColor = Color.Lime;
                    GB_ROTOR_Powermeter.Enabled = true;
                }
            }

           

            if (Status_HeartRateMonitor != _data.Status_HeartRateMonitor)
            {
                // Update
                Status_HeartRateMonitor = _data.Status_HeartRateMonitor;


                if (Status_HeartRateMonitor == -2)
                {
                    PB_LED_HeartRate_Monitor.BackColor = Color.Red;
                    LBL_Status_HeartrateMonitor.Enabled = true;
                }
                else if (Status_HeartRateMonitor == -1)
                {
                    PB_LED_HeartRate_Monitor.BackColor = Color.Silver;
                    LBL_Status_HeartrateMonitor.Enabled = false;
                }
                else if (Status_HeartRateMonitor == 0)
                {
                    PB_LED_HeartRate_Monitor.BackColor = Color.Gold;
                    LBL_Status_HeartrateMonitor.Enabled = true;
                }
                else if (Status_HeartRateMonitor == 1)
                {
                    PB_LED_HeartRate_Monitor.BackColor = Color.Lime;
                    LBL_Status_HeartrateMonitor.Enabled = true;
                }
            }



            if (Status_DataLogging != _data.Status_Datalogging)
            {
                // Update
                Status_DataLogging = _data.Status_Datalogging;


                if (Status_DataLogging == -2)
                {
                    PB_DataLogging.BackColor = Color.Red;
                }
                else if (Status_DataLogging == -1)
                {
                    PB_DataLogging.BackColor = Color.Silver;
                }
                else if (Status_DataLogging == 0)
                {
                    PB_DataLogging.BackColor = Color.Gold;

                }
                else if (Status_DataLogging == 1)
                {
                    PB_DataLogging.BackColor = Color.Lime;
                    
                }
            }

            // Intensity 

            int intensity = (int)Math.Round(SL_TestStim_Percentage.Value * 100.0 / SL_TestStim_Percentage.Maximum);
            /*
            if (intensity == _data.StimIntensity && LBL_I1.ForeColor.Equals(Color.Red))
            {
                LBL_I1.ForeColor = Color.Black;
                BT_UpdateAmplitude.BackColor = Color.Transparent;
                BT_UpdateAmplitude.ForeColor = Color.Black;
                BT_UpdateAmplitude.Visible = false;
            }
            if (intensity != _data.StimIntensity && LBL_I1.ForeColor.Equals(Color.Black))
            {
                LBL_I1.ForeColor = Color.Red;
                BT_UpdateAmplitude.BackColor = Color.Red;
                BT_UpdateAmplitude.ForeColor = Color.White;


                BT_UpdateAmplitude.Text = "Update Intensity";
                BT_UpdateAmplitude.Visible = true;
            }
            */
            if (intensity != _data.StimIntensity)
            {
                object sender = new object();
                EventArgs e = new EventArgs();
                SL_TestStim_Percentage.Value = _data.StimIntensity;                
                TestStim_Percentage_Scroll(sender, e);

            }


        }







        /// <summary>
        /// Tries to establish a new connection to the newly found server
        /// </summary>
        /// <param name="sender"></param>
        /// <param name="e"></param>
        private void connectUDPServer()
        {
            // Connect UDP Client
            udpClient = new UdpClient();
            udpClient.Client.Bind(new IPEndPoint(IPAddress.Any, UDP_Receive_Port));

            kill_Threads = false;

            // Starts new receive thread to receive UDP datagrams
            UDP_Receive_Thread = new Thread(new ThreadStart(this.receiveUDP_Data));
            UDP_Receive_Thread.Start();

            // Starts a new drawing thread to plot received data
            drawThread = new Thread(new ThreadStart(ChartWorker));
            drawThread.Start();
        }


        /// <summary>
        /// Disconnects a currently connected Server and frees resources
        /// </summary>
        /// <param name="sender"></param>
        /// <param name="e"></param>
        private void disconnectServer()
        {
            kill_Threads = true;
                                 

            if (udpClient != null)
            {
                udpClient.Close();
                udpClient = null;
            }

            startTicks = -1;
        }

        /// <summary>
        /// Tries to read a new Datagram from UDP
        /// </summary>
        private void receiveUDP_Data()
        {
            String line;
            
            var from = new IPEndPoint(0, 0);

            while (!kill_Threads)
            {

                try
                {
                    var recvBuffer = udpClient.Receive(ref from);
                    line = Encoding.UTF8.GetString(recvBuffer);
                    //Console.WriteLine(line);

                    interpretData(line);
                }
                catch (Exception e)
                {
                    Console.WriteLine("Error during receive: " + e.ToString());
                }

                //Thread.Sleep(1);
            }

        }

        long msg_cnt_old;
        long missing_message_CNT;
        /// <summary>
        /// Interprets a received Message and adds a datapoint to the queue
        /// </summary>
        /// <param name="data"></param>
        private void interpretData(String data)
        {

            UDP_Data udp_data = JsonConvert.DeserializeObject<UDP_Data>(data);

            Double X = udp_data.Timestamp;
            Double Y1 = 0.0;
            Double Y2 = 0.0;
                        
            // Data Selection for Y1
            if (idx_Y1 == 1)
            {
                Y1 = udp_data.LeftThighAngle;
                Y1_Unit = "°";
            }
            else if (idx_Y1 == 2)
            {
                Y1 = udp_data.RightThighAngle;
                Y1_Unit = "°";
            }

            else if (idx_Y1 == 3)
            {
                Y1 = udp_data.LeftThighAngle_normalized;
                Y1_Unit = "°";
            }
            else if (idx_Y1 == 4)
            {
                Y1 = udp_data.RightThighAngle_normalized;
                Y1_Unit = "°";
            }

            else if (idx_Y1 == 5)
            {
                Y1 = udp_data.LeftKneeAngle;
                Y1_Unit = "°";
            }

            else if (idx_Y1 == 6)
            {
                Y1 = udp_data.RightKneeAngle;
                Y1_Unit = "°";
            }

            else if (idx_Y1 == 7)
            {
                Y1 = udp_data.LeftKneeAngle_normalized;
                Y1_Unit = "°";
            }

            else if (idx_Y1 == 8)
            {
                Y1 = udp_data.RightKneeAngle_normalized;
                Y1_Unit = "°";
            }

            else if (idx_Y1 == 9)
            {
                Y1 = udp_data.CrankAngle_OpenDAQ;                
            }

            else if (idx_Y1 == 10)
            {
                Y1 = udp_data.CrankAngle_ROTOR;
                Y1_Unit = "°";
            }

            else if (idx_Y1 == 11)
            {
                Y1 = udp_data.CrankAngle_IMU_FOX;
                Y1_Unit = "°";
            }
            
            else if (idx_Y1 == 12)
            {
                Y1 = udp_data.Torque_HomeTrainer*1000;
                Y1_Unit = " mNm";
            }

            else if (idx_Y1 == 13)
            {
                Y1 = udp_data.Power_HomeTrainer;
                Y1_Unit = " W";
            }

            else if (idx_Y1 == 14)
            {
                Y1 = udp_data.Power_AVG_HomeTrainer;
                Y1_Unit = " W";
            }

            else if (idx_Y1 == 15)
            {
                Y1 = udp_data.Speed_HomeTrainer;
                Y1_Unit = " km/h";
            }

            else if (idx_Y1 == 16)
            {
                Y1 = udp_data.Speed_CyclingComputer;
                Y1_Unit = " km/h";
            }

            else if (idx_Y1 == 17)
            {
                Y1 = udp_data.Torque_Total_PowerMeter;
                Y1_Unit = " Nm";
            }
            else if (idx_Y1 == 18)
            {
                Y1 = udp_data.Power_Total_PowerMeter;
                Y1_Unit = " W";
            }

            else if (idx_Y1 == 19)
            {
                Y1 = udp_data.LoopTime;
                Y1_Unit = " ms";
            }

            else if (idx_Y1 == 21)
            {
                Y1 = udp_data.DebugValue;
                Y1_Unit = "";
            }

            // Data Selection for Y2
            if (idx_Y2 == 1)
            {
                Y2 = udp_data.LeftThighAngle;
                Y2_Unit = "°";
            }
            else if (idx_Y2 == 2)
            {
                Y2 = udp_data.RightThighAngle;
                Y2_Unit = "°";
            }

            else if (idx_Y2 == 3)
            {
                Y2 = udp_data.LeftThighAngle_normalized;
                Y2_Unit = "°";
            }
            else if (idx_Y2 == 4)
            {
                Y2 = udp_data.RightThighAngle_normalized;
                Y2_Unit = "°";
            }

            else if (idx_Y2 == 5)
            {
                Y2 = udp_data.LeftKneeAngle;
                Y2_Unit = "°";
            }

            else if (idx_Y2 == 6)
            {
                Y2 = udp_data.RightKneeAngle;
                Y2_Unit = "°";
            }

            else if (idx_Y2 == 7)
            {
                Y2 = udp_data.LeftKneeAngle_normalized;
                Y2_Unit = "°";
            }

            else if (idx_Y2 == 8)
            {
                Y2 = udp_data.RightKneeAngle_normalized;
                Y2_Unit = "°";
            }

            else if (idx_Y2 == 9)
            {
                Y2 = udp_data.CrankAngle_OpenDAQ;
                Y2_Unit = "°";
            }

            else if (idx_Y2 == 10)
            {
                Y2 = udp_data.CrankAngle_ROTOR;
                Y2_Unit = "°";
            }

            else if (idx_Y2 == 11)
            {
                Y2 = udp_data.CrankAngle_IMU_FOX;
                Y2_Unit = "°";
            }

            else if (idx_Y2 == 12)
            {
                Y2 = udp_data.Torque_HomeTrainer * 1000;
                Y2_Unit = " mNm";
            }

            else if (idx_Y2 == 13)
            {
                Y2 = udp_data.Power_HomeTrainer;
                Y2_Unit = " W";
            }

            else if (idx_Y2 == 14)
            {
                Y2 = udp_data.Power_AVG_HomeTrainer;
                Y2_Unit = " W";
            }

            else if (idx_Y2 == 15)
            {
                Y2 = udp_data.Speed_HomeTrainer;
                Y2_Unit = " km/h";
            }

            else if (idx_Y2 == 16)
            {
                Y2 = udp_data.Speed_CyclingComputer;
                Y2_Unit = " km/h";
            }

            else if (idx_Y2 == 17)
            {
                Y2 = udp_data.Torque_Total_PowerMeter;
                Y2_Unit = " Nm";
            }
            else if (idx_Y2 == 18)
            {
                Y2 = udp_data.Power_Total_PowerMeter;
                Y2_Unit = " W";
            }

            else if (idx_Y2 == 19)
            {
                Y2 = udp_data.LoopTime;
                Y2_Unit = " ms";
            }

            else if (idx_Y2 == 21)
            {
                Y2 = udp_data.DebugValue;
                Y2_Unit = "";
            }


            // Update Indicators and System States
            delegated_updateIndicatorsAndSystemStates(udp_data);



            if (startTicks == -1 || X < startTicks)
            {
                startTicks = X;
            }


            // Enqueue Data
            double x_value = (X - startTicks) ;
                              

            MyDataPoint _point = new MyDataPoint(x_value, Y1, Y2);
            lock (lockObject)
            {
                dataQueue.Enqueue(_point);
            }

            // Console.WriteLine("X=" + _point.X + ", Y=" + _point.Y);
        }

        /// <summary>
        /// Sets a new Position of the Zeroline
        /// </summary>
        private void updateZeroLine_Y1()
        {
            int x_Pos = PB_Plot.Location.X;

            int y_Offset = PB_Plot.Location.Y;

            int height = PB_Plot.Height;

            int y = (int)Math.Round(height * ((Y1_MAX - 0) / (Y1_MAX - Y1_MIN)));

            int y_Pos = y_Offset + y;

            PB_Zeroline_Y1.Location = new Point(x_Pos, y_Pos);
        }

        /// <summary>
        /// Sets a new Position of the Zeroline
        /// </summary>
        private void updateZeroLine_Y2()
        {
            int x_Pos = PB_Plot.Location.X;

            int y_Offset = PB_Plot.Location.Y;

            int height = PB_Plot.Height;

            int y = (int)Math.Round(height * ((Y2_MAX - 0) / (Y2_MAX - Y2_MIN)));

            int y_Pos = y_Offset + y;

            PB_Zeroline_Y2.Location = new Point(x_Pos, y_Pos);
        }

        /// <summary>
        /// WorkerMethod for Thread who is drawing the curves
        /// </summary>
        private void ChartWorker()
        {
            System.Globalization.CultureInfo customCulture = (System.Globalization.CultureInfo)System.Threading.Thread.CurrentThread.CurrentCulture.Clone();
            customCulture.NumberFormat.NumberDecimalSeparator = ".";

            System.Threading.Thread.CurrentThread.CurrentCulture = customCulture;

            while (!kill_Threads)
            {
                drawPlot();
                Thread.Sleep(SleepTime_ChartWorker);
            }
        }

        /// <summary>
        /// Draws the next Data Point in of the Queue_ECG
        /// </summary>
        private void drawPlot()
        {
            int width = PB_Plot.Width;
            int height = PB_Plot.Height;

            int i = 0;            

            while (dataQueue.Count > 0 && !kill_Threads)
            {
                MyDataPoint point = null;


                // Get next DataPoint
                if (dataQueue.Count > 0)
                {
                    point = dataQueue.Dequeue();                   
                }

                if (point == null)
                {
                    return; //nothing to draw
                }

                delegated_updateUDP_DataValue(point);

                // Calc X-Value
                int x = (int)(width * ((point.X - Math.Truncate(point.X / X_MAX) * X_MAX)) / X_MAX);

                // Calc Y-Values
                int y1 = (int)Math.Round(height * ((Y1_MAX - point.Y1) / (Y1_MAX - Y1_MIN)));
                int y2 = (int)Math.Round(height * ((Y2_MAX - point.Y2) / (Y2_MAX - Y2_MIN)));

                if (y1 > height)
                {
                    y1 = height;
                }
                else if (y1 < 0)
                {
                    y1 = 0;
                }

                if (y2 > height)
                {
                    y2 = height;
                }
                else if (y2 < 0)
                {
                    y2 = 0;
                }

                Point newPoint1 = new Point(x, y1);
                Point newPoint2 = new Point(x, y2);

                // FirstPoint ever?
                if (dataPoint1 == null)
                {
                    dataPoint1 = newPoint1;
                    dataPoint2 = newPoint2;
                    return;
                }

                // new Periode?
                if (newPoint1.X < dataPoint1.X)
                {
                    dataPoint1 = newPoint1;
                    dataPoint2 = newPoint2;
                    return;
                }


                // DRAAAAAAAAAAWING :)

                Graphics g = PB_Plot.CreateGraphics();
                //Random r = new Random();

                g.FillRectangle(new System.Drawing.SolidBrush(Color.White), new Rectangle(x, 0, 50, height));

                if (idx_Y1 > 0)
                {
                    g.DrawLine(new Pen(color_Y1, 3F), dataPoint1, newPoint1);
                }

                if (idx_Y2 > 0)
                {
                    g.DrawLine(new Pen(color_Y2, 3F), dataPoint2, newPoint2);
                }
                
                dataPoint1 = newPoint1;
                dataPoint2 = newPoint2;

            }
        }

        /// <summary>
        /// Ends the application
        /// </summary>
        /// <param name="sender"></param>
        /// <param name="e"></param>
        private void button1_Click(object sender, EventArgs e)
        {
            kill_Threads = true;
                  

            if (udpClient != null)
            {
                udpClient.Close();
            }

            System.Environment.Exit(1);
        }

        private void BT_StimON_Click(object sender, EventArgs e)
        {
            if (BT_TestStim.Text.Equals("TestStim ON")){

                TCP_Message_TestStim testStim = new TCP_Message_TestStim();

                testStim.I_percent = SL_TestStim_Percentage.Value;

                testStim.CH_Active = new bool[] {   CB_Ch1_active.Checked,
                                                CB_Ch2_active.Checked,
                                                CB_Ch3_active.Checked,
                                                CB_Ch4_active.Checked,
                                                CB_Ch5_active.Checked,
                                                CB_Ch6_active.Checked,
                                                CB_Ch7_active.Checked,
                                                CB_Ch8_active.Checked };
                testStim.Burst_Duration = -1;

                String JSON = JsonConvert.SerializeObject(testStim);

                tcpClient.sendMessage(CMD_SET_TEST_STIMULATION + "@" + JSON);

                BT_TestStim.Text = "TestStim OFF";


            }
            else
            {
                TCP_Message_TestStim testStim = new TCP_Message_TestStim();

                testStim.I_percent = 0;

                testStim.CH_Active = new bool[] { false, false, false, false, false, false, false, false };
        
                String JSON = JsonConvert.SerializeObject(testStim);

                tcpClient.sendMessage(CMD_SET_TEST_STIMULATION + "@" + JSON);

                BT_TestStim.Text = "TestStim ON";
            }
        }

        private void BT_TestBurst_Click(object sender, EventArgs e)
        {
            TCP_Message_TestStim testStim = new TCP_Message_TestStim();

            testStim.I_percent = (float)SL_TestStim_Percentage.Value/ (float)SL_TestStim_Percentage.Maximum;

            testStim.CH_Active = new bool[] {   CB_Ch1_active.Checked,
                                                CB_Ch2_active.Checked,
                                                CB_Ch3_active.Checked,
                                                CB_Ch4_active.Checked,
                                                CB_Ch5_active.Checked,
                                                CB_Ch6_active.Checked,
                                                CB_Ch7_active.Checked,
                                                CB_Ch8_active.Checked };

            testStim.Burst_Duration = Double.Parse(TB_BurstDuration.Text);

            String JSON = JsonConvert.SerializeObject(testStim);

            tcpClient.sendMessage(CMD_SET_TEST_STIMULATION + "@" + JSON);
        }



        private void TestStim_Percentage_Scroll(object sender, EventArgs e)
        {

            I_TestStim.Text = SL_TestStim_Percentage.Value.ToString();

            try
            {
                // Update real Current Values
                double i1 = Double.Parse(TB_Imax1.Text) * (double)(SL_TestStim_Percentage.Value) / (double)(SL_TestStim_Percentage.Maximum);
                double i2 = Double.Parse(TB_Imax2.Text) * (double)(SL_TestStim_Percentage.Value) / (double)(SL_TestStim_Percentage.Maximum);
                double i3 = Double.Parse(TB_Imax3.Text) * (double)(SL_TestStim_Percentage.Value) / (double)(SL_TestStim_Percentage.Maximum);
                double i4 = Double.Parse(TB_Imax4.Text) * (double)(SL_TestStim_Percentage.Value) / (double)(SL_TestStim_Percentage.Maximum);
                double i5 = Double.Parse(TB_Imax5.Text) * (double)(SL_TestStim_Percentage.Value) / (double)(SL_TestStim_Percentage.Maximum);
                double i6 = Double.Parse(TB_Imax6.Text) * (double)(SL_TestStim_Percentage.Value) / (double)(SL_TestStim_Percentage.Maximum);
                double i7 = Double.Parse(TB_Imax7.Text) * (double)(SL_TestStim_Percentage.Value) / (double)(SL_TestStim_Percentage.Maximum);
                double i8 = Double.Parse(TB_Imax8.Text) * (double)(SL_TestStim_Percentage.Value) / (double)(SL_TestStim_Percentage.Maximum);
            

            LBL_I1.Text = "(" + (int)i1 + "mA)";
            LBL_I2.Text = "(" + (int)i2 + "mA)";
            LBL_I3.Text = "(" + (int)i3 + "mA)";
            LBL_I4.Text = "(" + (int)i4 + "mA)";
            LBL_I5.Text = "(" + (int)i5 + "mA)";
            LBL_I6.Text = "(" + (int)i6 + "mA)";
            LBL_I7.Text = "(" + (int)i7 + "mA)";
            LBL_I8.Text = "(" + (int)i8 + "mA)";
            }
            catch (Exception exception)
            {
            }


        }

        private void label39_Click(object sender, EventArgs e)
        {

        }

        private void button3_Click(object sender, EventArgs e)
        {
            tcpClient.sendMessage(CMD_GET_STIM_PARAMS + "@");
        }

        private void Connection_Text_Click(object sender, EventArgs e)
        {
        }

        private void tabPage1_Click(object sender, EventArgs e)
        {

        }

        private void RB_Left_ThighAngle_CheckedChanged(object sender, EventArgs e)
        {
            Y1_MIN = -90;
            Y1_MAX = 90;

            Y2_MIN = -90;
            Y2_MAX = 90;

            LBL_Y1_MIN.Text = Y1_MIN.ToString();
            LBL_Y1_MAX.Text = Y1_MAX.ToString();

            updateZeroLine_Y1();
        }

        private void RB_Right_ThighAngle_CheckedChanged(object sender, EventArgs e)
        {
            Y1_MIN = -90;
            Y1_MAX = 90;

            LBL_Y1_MIN.Text = Y1_MIN.ToString();
            LBL_Y1_MAX.Text = Y1_MAX.ToString();

            updateZeroLine_Y1();
        }

        private void RB_Left_KneeAngle_CheckedChanged(object sender, EventArgs e)
        {
            Y1_MIN = -180;
            Y1_MAX = 180;

            LBL_Y1_MIN.Text = Y1_MIN.ToString();
            LBL_Y1_MAX.Text = Y1_MAX.ToString();

            updateZeroLine_Y1();
        }
        
        private void RB_Right_KneeAngle_CheckedChanged(object sender, EventArgs e)
        {
            Y1_MIN = -180;
            Y1_MAX = 180;

            LBL_Y1_MIN.Text = Y1_MIN.ToString();
            LBL_Y1_MAX.Text = Y1_MAX.ToString();

            updateZeroLine_Y1();
        }

        private void RB_CrankAngle_CheckedChanged(object sender, EventArgs e)
        {
            Y1_MIN = 0;
            Y1_MAX = 360;

            LBL_Y1_MIN.Text = Y1_MIN.ToString();
            LBL_Y1_MAX.Text = Y1_MAX.ToString();

            updateZeroLine_Y1();
        }


        private void RB_BiodexPosition_CheckedChanged(object sender, EventArgs e)
        {
            Y1_MIN = 25;
            Y1_MAX = 180;

            LBL_Y1_MIN.Text = Y1_MIN.ToString();
            LBL_Y1_MAX.Text = Y1_MAX.ToString();

            updateZeroLine_Y1();
        }

        private void BT_Update_IMUSEF_Click(object sender, EventArgs e)
        {
            BT_load_config_from_IMUSEF.Enabled = false;
            BT_Update_IMUSEF.Enabled = false;
            BT_TestStim.Enabled = false;
            BT_TestBurst.Enabled = false;

            IMUSEF_StimConfig new_params = new IMUSEF_StimConfig();

            new_params.F = Double.Parse(TB_F.Text);
            new_params.F_Boost = Double.Parse(TB_F_BOOST.Text);

            new_params.Monophasic = new bool[] {    CB_MonoPh_1.Checked,
                                                    CB_MonoPh_2.Checked,
                                                    CB_MonoPh_3.Checked,
                                                    CB_MonoPh_4.Checked,
                                                    CB_MonoPh_5.Checked,
                                                    CB_MonoPh_6.Checked,
                                                    CB_MonoPh_7.Checked,
                                                    CB_MonoPh_8.Checked};

            new_params.PhW = new int[] { int.Parse(TB_PhW1.Text),
                                         int.Parse(TB_PhW2.Text),
                                         int.Parse(TB_PhW3.Text),
                                         int.Parse(TB_PhW4.Text),
                                         int.Parse(TB_PhW5.Text),
                                         int.Parse(TB_PhW6.Text),
                                         int.Parse(TB_PhW7.Text),
                                         int.Parse(TB_PhW8.Text) };

            new_params.PhW_Boost = new int[] {  int.Parse(TB_PhW1_BOOST.Text),
                                                int.Parse(TB_PhW2_BOOST.Text),
                                                int.Parse(TB_PhW3_BOOST.Text),
                                                int.Parse(TB_PhW4_BOOST.Text),
                                                int.Parse(TB_PhW5_BOOST.Text),
                                                int.Parse(TB_PhW6_BOOST.Text),
                                                int.Parse(TB_PhW7_BOOST.Text),
                                                int.Parse(TB_PhW8_BOOST.Text) };

            new_params.IPG = new int[] { int.Parse(TB_IPG1.Text),
                                         int.Parse(TB_IPG2.Text),
                                         int.Parse(TB_IPG3.Text),
                                         int.Parse(TB_IPG4.Text),
                                         int.Parse(TB_IPG5.Text),
                                         int.Parse(TB_IPG6.Text),
                                         int.Parse(TB_IPG7.Text),
                                         int.Parse(TB_IPG8.Text) };

            new_params.I_Max = new int[] { int.Parse(TB_Imax1.Text),
                                           int.Parse(TB_Imax2.Text),
                                           int.Parse(TB_Imax3.Text),
                                           int.Parse(TB_Imax4.Text),
                                           int.Parse(TB_Imax5.Text),
                                           int.Parse(TB_Imax6.Text),
                                           int.Parse(TB_Imax7.Text),
                                           int.Parse(TB_Imax8.Text) };

            new_params.RampUP = new int[] { int.Parse(TB_Ramp_UP1.Text),
                                           int.Parse(TB_Ramp_UP2.Text),
                                           int.Parse(TB_Ramp_UP3.Text),
                                           int.Parse(TB_Ramp_UP4.Text),
                                           int.Parse(TB_Ramp_UP5.Text),
                                           int.Parse(TB_Ramp_UP6.Text),
                                           int.Parse(TB_Ramp_UP7.Text),
                                           int.Parse(TB_Ramp_UP8.Text) };

            new_params.RampDOWN = new int[] { int.Parse(TB_Ramp_DOWN1.Text),
                                           int.Parse(TB_Ramp_DOWN2.Text),
                                           int.Parse(TB_Ramp_DOWN3.Text),
                                           int.Parse(TB_Ramp_DOWN4.Text),
                                           int.Parse(TB_Ramp_DOWN5.Text),
                                           int.Parse(TB_Ramp_DOWN6.Text),
                                           int.Parse(TB_Ramp_DOWN7.Text),
                                           int.Parse(TB_Ramp_DOWN8.Text) };

            String JSON = JsonConvert.SerializeObject(new_params);

            tcpClient.sendMessage(CMD_SET_STIM_PARAMS + "@" + JSON);

        }

        private void TB_Imax1_TextChanged(object sender, EventArgs e)
        {
            TestStim_Percentage_Scroll(sender, e);
        }

        private void TB_Imax2_TextChanged(object sender, EventArgs e)
        {
            TestStim_Percentage_Scroll(sender, e);
        }

        private void TB_Imax3_TextChanged(object sender, EventArgs e)
        {
            TestStim_Percentage_Scroll(sender, e);
        }

        private void TB_Imax4_TextChanged(object sender, EventArgs e)
        {
            TestStim_Percentage_Scroll(sender, e);
        }

        private void TB_Imax5_TextChanged(object sender, EventArgs e)
        {
            TestStim_Percentage_Scroll(sender, e);
        }

        private void TB_Imax6_TextChanged(object sender, EventArgs e)
        {
            TestStim_Percentage_Scroll(sender, e);
        }

        private void TB_Imax7_TextChanged(object sender, EventArgs e)
        {
            TestStim_Percentage_Scroll(sender, e);
        }

        private void TB_Imax8_TextChanged(object sender, EventArgs e)
        {
            TestStim_Percentage_Scroll(sender, e);
        }

        private void label44_Click(object sender, EventArgs e)
        {

        }

        private void tabPage3_Click(object sender, EventArgs e)
        {

        }

        private void updateIMUSEF_ControllerConfig()
        {
            IMUSEF_ControllerConfig config;

            if (RB_Control_CrankAngle.Checked)
            {
                config = imusef_config.CrankAngle_ControllerConfig;
            }
            else if (RB_Control_KneeAngle.Checked)
            {
                config = imusef_config.KneeAngle_ControllerConfig;
            }
            else if (RB_Control_ThighAngle.Checked)
            {
                config = imusef_config.ThighAngle_ControllerConfig;
            }
            else if (RB_Control_Observer.Checked)
            {
                config = imusef_config.Observer_ControllerConfig;
            }
            else if (RB_Control_Biodex.Checked)
            {
                config = imusef_config.Biodex_ControllerConfig;
            }
            else
            {
                return;
            }


            config.Start[0] = SL_START_CH1.Value;
            config.Stop[0] = SL_STOP_CH1.Value;

            config.Start[1] = SL_START_CH2.Value;
            config.Stop[1] = SL_STOP_CH2.Value;

            config.Start[2] = SL_START_CH3.Value;
            config.Stop[2] = SL_STOP_CH3.Value;

            config.Start[3] = SL_START_CH4.Value;
            config.Stop[3] = SL_STOP_CH4.Value;

            config.Start[4] = SL_START_CH5.Value;
            config.Stop[4] = SL_STOP_CH5.Value;

            config.Start[5] = SL_START_CH6.Value;
            config.Stop[5] = SL_STOP_CH6.Value;

            config.Start[6] = SL_START_CH7.Value;
            config.Stop[6] = SL_STOP_CH7.Value;
        
            config.Start[7] = SL_START_CH8.Value;
            config.Stop[7] = SL_STOP_CH8.Value;


        }

        private void SL_START_CH1_Scroll(object sender, EventArgs e)
        {

            TB_START_Ch1.Text = SL_START_CH1.Value.ToString();
            TB_STOP_Ch1.Text = SL_STOP_CH1.Value.ToString();

            updateIMUSEF_ControllerConfig();          

            int height = PB_Indicator_CH1.Height;
            int width = PB_Indicator_CH1.Width;

            // Translate values to dimensions of the picture box
            int start = (int)((double)width * ((double)SL_START_CH1.Value - (double)SL_START_CH1.Minimum) / ((double)SL_START_CH1.Maximum - (double)SL_START_CH1.Minimum));
            int stop = (int)((double)width * ((double)SL_STOP_CH1.Value - (double)SL_STOP_CH1.Minimum) / ((double)SL_STOP_CH1.Maximum - (double)SL_STOP_CH1.Minimum));

            Bitmap image = new Bitmap(width, height);
            Graphics g = Graphics.FromImage(image);

            g.FillRectangle(new System.Drawing.SolidBrush(Color.White), new Rectangle(0, 0, width, height));

            if (start == stop)
            {}

            else if (start < stop)
            {
                g.FillRectangle(new System.Drawing.SolidBrush(Color.Lime), new Rectangle(start, 0, stop - start, height));
            }
            else
            {
                g.FillRectangle(new System.Drawing.SolidBrush(Color.Lime), new Rectangle(0, 0, stop, height));
                g.FillRectangle(new System.Drawing.SolidBrush(Color.Lime), new Rectangle(start, 0, width - start, height));
            }

            PB_Indicator_CH1.Image = image;


        }

        private void SL_STOP_CH1_Scroll(object sender, EventArgs e)
        {
            SL_START_CH1_Scroll(sender, e);
        }

        private void SL_START_CH3_Scroll(object sender, EventArgs e)
        {

            TB_START_Ch3.Text = SL_START_CH3.Value.ToString();
            TB_STOP_Ch3.Text = SL_STOP_CH3.Value.ToString();

            updateIMUSEF_ControllerConfig();

            int height = PB_Indicator_CH3.Height;
            int width = PB_Indicator_CH3.Width;

            // Translate values to dimensions of the picture box
            int start = (int)((double)width * ((double)SL_START_CH3.Value - (double)SL_START_CH3.Minimum) / ((double)SL_START_CH3.Maximum - (double)SL_START_CH3.Minimum));
            int stop = (int)((double)width * ((double)SL_STOP_CH3.Value - (double)SL_STOP_CH3.Minimum) / ((double)SL_STOP_CH3.Maximum - (double)SL_STOP_CH3.Minimum));

            Bitmap image = new Bitmap(width, height);
            Graphics g = Graphics.FromImage(image);

            g.FillRectangle(new System.Drawing.SolidBrush(Color.White), new Rectangle(0, 0, width, height));

            if (start == stop)
            { }

            else if (start < stop)
            {
                g.FillRectangle(new System.Drawing.SolidBrush(Color.Lime), new Rectangle(start, 0, stop - start, height));
            }
            else
            {
                g.FillRectangle(new System.Drawing.SolidBrush(Color.Lime), new Rectangle(0, 0, stop, height));
                g.FillRectangle(new System.Drawing.SolidBrush(Color.Lime), new Rectangle(start, 0, width - start, height));
            }

            PB_Indicator_CH3.Image = image;

        }

        private void SL_START_CH5_Scroll(object sender, EventArgs e)
        {
            
            TB_START_Ch5.Text = SL_START_CH5.Value.ToString();
            TB_STOP_Ch5.Text = SL_STOP_CH5.Value.ToString();

            updateIMUSEF_ControllerConfig();

            int height = PB_Indicator_CH5.Height;
            int width = PB_Indicator_CH5.Width;

            // Translate values to dimensions of the picture box
            int start = (int)((double)width * ((double)SL_START_CH5.Value - (double)SL_START_CH5.Minimum) / ((double)SL_START_CH5.Maximum - (double)SL_START_CH5.Minimum));
            int stop = (int)((double)width * ((double)SL_STOP_CH5.Value - (double)SL_STOP_CH5.Minimum) / ((double)SL_STOP_CH5.Maximum - (double)SL_STOP_CH5.Minimum));

            Bitmap image = new Bitmap(width, height);
            Graphics g = Graphics.FromImage(image);

            g.FillRectangle(new System.Drawing.SolidBrush(Color.White), new Rectangle(0, 0, width, height));

            if (start == stop)
            { }

            else if (start < stop)
            {
                g.FillRectangle(new System.Drawing.SolidBrush(Color.Lime), new Rectangle(start, 0, stop - start, height));
            }
            else
            {
                g.FillRectangle(new System.Drawing.SolidBrush(Color.Lime), new Rectangle(0, 0, stop, height));
                g.FillRectangle(new System.Drawing.SolidBrush(Color.Lime), new Rectangle(start, 0, width - start, height));
            }


            PB_Indicator_CH5.Image = image;
        }

        private void SL_START_CH7_Scroll(object sender, EventArgs e)
        {
           
            TB_START_Ch7.Text = SL_START_CH7.Value.ToString();
            TB_STOP_Ch7.Text = SL_STOP_CH7.Value.ToString();

            updateIMUSEF_ControllerConfig();

            int height = PB_Indicator_CH7.Height;
            int width = PB_Indicator_CH7.Width;

            // Translate values to dimensions of the picture box
            int start = (int)((double)width * ((double)SL_START_CH7.Value - (double)SL_START_CH7.Minimum) / ((double)SL_START_CH7.Maximum - (double)SL_START_CH7.Minimum));
            int stop = (int)((double)width * ((double)SL_STOP_CH7.Value - (double)SL_STOP_CH7.Minimum) / ((double)SL_STOP_CH7.Maximum - (double)SL_STOP_CH7.Minimum));

            Bitmap image = new Bitmap(width, height);
            Graphics g = Graphics.FromImage(image);

            g.FillRectangle(new System.Drawing.SolidBrush(Color.White), new Rectangle(0, 0, width, height));

            if (start == stop)
            { }

            else if (start < stop)
            {
                g.FillRectangle(new System.Drawing.SolidBrush(Color.Lime), new Rectangle(start, 0, stop - start, height));
            }
            else
            {
                g.FillRectangle(new System.Drawing.SolidBrush(Color.Lime), new Rectangle(0, 0, stop, height));
                g.FillRectangle(new System.Drawing.SolidBrush(Color.Lime), new Rectangle(start, 0, width - start, height));
            }


            PB_Indicator_CH7.Image = image;
        }

        private void SL_START_CH2_Scroll(object sender, EventArgs e)
        {
            

            TB_START_Ch2.Text = SL_START_CH2.Value.ToString();
            TB_STOP_Ch2.Text = SL_STOP_CH2.Value.ToString();

            updateIMUSEF_ControllerConfig();

            int height = PB_Indicator_CH2.Height;
            int width = PB_Indicator_CH2.Width;

            // Translate values to dimensions of the picture box
            int start = (int)((double)width * ((double)SL_START_CH2.Value - (double)SL_START_CH2.Minimum) / ((double)SL_START_CH2.Maximum - (double)SL_START_CH2.Minimum));
            int stop = (int)((double)width * ((double)SL_STOP_CH2.Value - (double)SL_STOP_CH2.Minimum) / ((double)SL_STOP_CH2.Maximum - (double)SL_STOP_CH2.Minimum));

            Bitmap image = new Bitmap(width, height);
            Graphics g = Graphics.FromImage(image);

            g.FillRectangle(new System.Drawing.SolidBrush(Color.White), new Rectangle(0, 0, width, height));

            if (start == stop)
            { }

            else if (start < stop)
            {
                g.FillRectangle(new System.Drawing.SolidBrush(Color.Lime), new Rectangle(start, 0, stop - start, height));
            }
            else
            {
                g.FillRectangle(new System.Drawing.SolidBrush(Color.Lime), new Rectangle(0, 0, stop, height));
                g.FillRectangle(new System.Drawing.SolidBrush(Color.Lime), new Rectangle(start, 0, width - start, height));
            }


            PB_Indicator_CH2.Image = image;
        }

        private void SL_START_CH4_Scroll(object sender, EventArgs e)
        {
            

            TB_START_Ch4.Text = SL_START_CH4.Value.ToString();
            TB_STOP_Ch4.Text = SL_STOP_CH4.Value.ToString();

            updateIMUSEF_ControllerConfig();

            int height = PB_Indicator_CH4.Height;
            int width = PB_Indicator_CH4.Width;

            // Translate values to dimensions of the picture box
            int start = (int)((double)width * ((double)SL_START_CH4.Value - (double)SL_START_CH4.Minimum) / ((double)SL_START_CH4.Maximum - (double)SL_START_CH4.Minimum));
            int stop = (int)((double)width * ((double)SL_STOP_CH4.Value - (double)SL_STOP_CH4.Minimum) / ((double)SL_STOP_CH4.Maximum - (double)SL_STOP_CH4.Minimum));

            Bitmap image = new Bitmap(width, height);
            Graphics g = Graphics.FromImage(image);

            g.FillRectangle(new System.Drawing.SolidBrush(Color.White), new Rectangle(0, 0, width, height));

            if (start == stop)
            { }

            else if (start < stop)
            {
                g.FillRectangle(new System.Drawing.SolidBrush(Color.Lime), new Rectangle(start, 0, stop - start, height));
            }
            else
            {
                g.FillRectangle(new System.Drawing.SolidBrush(Color.Lime), new Rectangle(0, 0, stop, height));
                g.FillRectangle(new System.Drawing.SolidBrush(Color.Lime), new Rectangle(start, 0, width - start, height));
            }


            PB_Indicator_CH4.Image = image;
        }

        private void SL_START_CH6_Scroll(object sender, EventArgs e)
        {
            

            TB_START_Ch6.Text = SL_START_CH6.Value.ToString();
            TB_STOP_Ch6.Text = SL_STOP_CH6.Value.ToString();

            updateIMUSEF_ControllerConfig();

            int height = PB_Indicator_CH6.Height;
            int width = PB_Indicator_CH6.Width;

            // Translate values to dimensions of the picture box
            int start = (int)((double)width * ((double)SL_START_CH6.Value - (double)SL_START_CH6.Minimum) / ((double)SL_START_CH6.Maximum - (double)SL_START_CH6.Minimum));
            int stop = (int)((double)width * ((double)SL_STOP_CH6.Value - (double)SL_STOP_CH6.Minimum) / ((double)SL_STOP_CH6.Maximum - (double)SL_STOP_CH6.Minimum));

            Bitmap image = new Bitmap(width, height);
            Graphics g = Graphics.FromImage(image);

            g.FillRectangle(new System.Drawing.SolidBrush(Color.White), new Rectangle(0, 0, width, height));

            if (start == stop)
            { }

            else if (start < stop)
            {
                g.FillRectangle(new System.Drawing.SolidBrush(Color.Lime), new Rectangle(start, 0, stop - start, height));
            }
            else
            {
                g.FillRectangle(new System.Drawing.SolidBrush(Color.Lime), new Rectangle(0, 0, stop, height));
                g.FillRectangle(new System.Drawing.SolidBrush(Color.Lime), new Rectangle(start, 0, width - start, height));
            }


            PB_Indicator_CH6.Image = image;
        }

        private void SL_START_CH8_Scroll(object sender, EventArgs e)
        {
            

            TB_START_Ch8.Text = SL_START_CH8.Value.ToString();
            TB_STOP_Ch8.Text = SL_STOP_CH8.Value.ToString();

            updateIMUSEF_ControllerConfig();

            int height = PB_Indicator_CH8.Height;
            int width = PB_Indicator_CH8.Width;

            // Translate values to dimensions of the picture box
            int start = (int)((double)width * ((double)SL_START_CH8.Value - (double)SL_START_CH8.Minimum) / ((double)SL_START_CH8.Maximum - (double)SL_START_CH8.Minimum));
            int stop = (int)((double)width * ((double)SL_STOP_CH8.Value - (double)SL_STOP_CH8.Minimum) / ((double)SL_STOP_CH8.Maximum - (double)SL_STOP_CH8.Minimum));

            Bitmap image = new Bitmap(width, height);
            Graphics g = Graphics.FromImage(image);

            g.FillRectangle(new System.Drawing.SolidBrush(Color.White), new Rectangle(0, 0, width, height));

            if (start == stop)
            { }

            else if (start < stop)
            {
                g.FillRectangle(new System.Drawing.SolidBrush(Color.Lime), new Rectangle(start, 0, stop - start, height));
            }
            else
            {
                g.FillRectangle(new System.Drawing.SolidBrush(Color.Lime), new Rectangle(0, 0, stop, height));
                g.FillRectangle(new System.Drawing.SolidBrush(Color.Lime), new Rectangle(start, 0, width - start, height));
            }


            PB_Indicator_CH8.Image = image;
        }

        private void SL_STOP_CH3_Scroll(object sender, EventArgs e)
        {

            SL_START_CH3_Scroll(sender, e);
        }

        private void SL_STOP_CH5_Scroll(object sender, EventArgs e)
        {

            SL_START_CH5_Scroll(sender, e);
        }

        private void SL_STOP_CH7_Scroll(object sender, EventArgs e)
        {

            SL_START_CH7_Scroll(sender, e);
        }

        private void SL_STOP_CH2_Scroll(object sender, EventArgs e)
        {
            SL_START_CH2_Scroll(sender, e);
        }

        private void SL_STOP_CH4_Scroll(object sender, EventArgs e)
        {
            SL_START_CH4_Scroll(sender, e);
        }

        private void SL_STOP_CH6_Scroll(object sender, EventArgs e)
        {
            SL_START_CH6_Scroll(sender, e);
        }

        private void SL_STOP_CH8_Scroll(object sender, EventArgs e)
        {
            SL_START_CH8_Scroll(sender, e);
        }

        private void textBox5_TextChanged(object sender, EventArgs e)
        {

        }

        private void textBox9_TextChanged(object sender, EventArgs e)
        {

        }

        private void BT_load_config_from_file_Click(object sender, EventArgs e)
        {

             OpenFileDialog openFileDialog = new OpenFileDialog()
             {
                FileName = "Select file",
                Filter = "IMUSEF files (*.imusef)|*.imusef",
                Title = "Open IMUSEF - Configuration"
             };

            if (openFileDialog.ShowDialog() == DialogResult.OK)
            {
                try
                {
                    this.FilePath = openFileDialog.FileName;
                    String[] str_parts = this.FilePath.Split('\\');  
                        
                    LBL_Filename.Text = "Current File: " + str_parts[str_parts.Length-1];                    

                    String JSON = System.IO.File.ReadAllText(FilePath);

                    imusef_config = JsonConvert.DeserializeObject<IMUSEF_Config>(JSON);

                    // MessageBox.Show(JSON);

                    updateStimConfig(imusef_config.StimConfig);
                    RB_Control_CrankAngle_CheckedChanged(sender, e);
                    



                }
                catch (Exception ex)
                {
                   
                }
            }
        }


        private void button2_Click(object sender, EventArgs e)
        {
            // Displays a SaveFileDialog so the user can save the Image  
            // assigned to Button2.  
            SaveFileDialog saveFileDialog1 = new SaveFileDialog();
            saveFileDialog1.Filter = "IMUSEF Configuration|*.imusef";
            saveFileDialog1.Title = "Save an IMUSEF Configuration";
            saveFileDialog1.ShowDialog();

            SaveFile(saveFileDialog1.FileName);

        }

        private void SaveFile(String File)
        {
            // If the file name is not an empty string open it for saving.  
            if (!File.Equals(""))
            {
                // Get the Configration of the Stimulator

                imusef_config.StimConfig.F = Double.Parse(TB_F.Text);
                imusef_config.StimConfig.F_Boost = Double.Parse(TB_F_BOOST.Text);

                imusef_config.StimConfig.PhW = new int[] {   int.Parse(TB_PhW1.Text),
                                                             int.Parse(TB_PhW2.Text),
                                                             int.Parse(TB_PhW3.Text),
                                                             int.Parse(TB_PhW4.Text),
                                                             int.Parse(TB_PhW5.Text),
                                                             int.Parse(TB_PhW6.Text),
                                                             int.Parse(TB_PhW7.Text),
                                                             int.Parse(TB_PhW8.Text) };

                imusef_config.StimConfig.IPG = new int[] {   int.Parse(TB_IPG1.Text),
                                                             int.Parse(TB_IPG2.Text),
                                                             int.Parse(TB_IPG3.Text),
                                                             int.Parse(TB_IPG4.Text),
                                                             int.Parse(TB_IPG5.Text),
                                                             int.Parse(TB_IPG6.Text),
                                                             int.Parse(TB_IPG7.Text),
                                                             int.Parse(TB_IPG8.Text) };

                imusef_config.StimConfig.I_Max = new int[] {    int.Parse(TB_Imax1.Text),
                                                               int.Parse(TB_Imax2.Text),
                                                               int.Parse(TB_Imax3.Text),
                                                               int.Parse(TB_Imax4.Text),
                                                               int.Parse(TB_Imax5.Text),
                                                               int.Parse(TB_Imax6.Text),
                                                               int.Parse(TB_Imax7.Text),
                                                               int.Parse(TB_Imax8.Text) };

                imusef_config.StimConfig.RampUP = new int[] {  int.Parse(TB_Ramp_UP1.Text),
                                                               int.Parse(TB_Ramp_UP2.Text),
                                                               int.Parse(TB_Ramp_UP3.Text),
                                                               int.Parse(TB_Ramp_UP4.Text),
                                                               int.Parse(TB_Ramp_UP5.Text),
                                                               int.Parse(TB_Ramp_UP6.Text),
                                                               int.Parse(TB_Ramp_UP7.Text),
                                                               int.Parse(TB_Ramp_UP8.Text) };

                imusef_config.StimConfig.RampDOWN = new int[] {    int.Parse(TB_Ramp_DOWN1.Text),
                                                                   int.Parse(TB_Ramp_DOWN2.Text),
                                                                   int.Parse(TB_Ramp_DOWN3.Text),
                                                                   int.Parse(TB_Ramp_DOWN4.Text),
                                                                   int.Parse(TB_Ramp_DOWN5.Text),
                                                                   int.Parse(TB_Ramp_DOWN6.Text),
                                                                   int.Parse(TB_Ramp_DOWN7.Text),
                                                                   int.Parse(TB_Ramp_DOWN8.Text) };


                String JSON = JsonConvert.SerializeObject(imusef_config, Formatting.Indented);

                // Finally write the actual file
                System.IO.File.WriteAllText(File, JSON);

                MessageBox.Show("Successfully saved configuration to file: \n" + File);

                this.FilePath = File;

                String[] str_parts = this.FilePath.Split('\\');

                LBL_Filename.Text = "Current File: " + str_parts[str_parts.Length - 1];
            }
        }

        private void activateTCPControllerElements()
        {
            BT_TestStim.Text = "TestStim ON";

            // All Disabled
            if (tcpClient.STATE != myTCP_Client.CONNECTED)

            {

                CB_Ch1_active.Enabled = false;
                CB_Ch2_active.Enabled = false;
                CB_Ch3_active.Enabled = false;
                CB_Ch4_active.Enabled = false;
                CB_Ch5_active.Enabled = false;
                CB_Ch6_active.Enabled = false;
                CB_Ch7_active.Enabled = false;
                CB_Ch8_active.Enabled = false;
                
                BT_TestStim.Enabled = false;
                BT_TestBurst.Enabled = false;
                return;

            }

            


            if (CMB_Controller.SelectedIndex == 0)
            {

                CB_Ch1_active.Enabled = true;
                CB_Ch2_active.Enabled = true;
                CB_Ch3_active.Enabled = true;
                CB_Ch4_active.Enabled = true;
                CB_Ch5_active.Enabled = true;
                CB_Ch6_active.Enabled = true;
                CB_Ch7_active.Enabled = true;
                CB_Ch8_active.Enabled = true;


                if (Status_Stimulator == 1)
                {
                    BT_TestStim.Enabled = true;
                    BT_TestBurst.Enabled = true;
                }
            }

            else
            {
                CB_Ch1_active.Enabled = false;
                CB_Ch2_active.Enabled = false;
                CB_Ch3_active.Enabled = false;
                CB_Ch4_active.Enabled = false;
                CB_Ch5_active.Enabled = false;
                CB_Ch6_active.Enabled = false;
                CB_Ch7_active.Enabled = false;
                CB_Ch8_active.Enabled = false;

                BT_TestStim.Enabled = false;
                BT_TestBurst.Enabled = false;


            }        

        }
                

        private void updateAlgorithmTab(IMUSEF_ControllerConfig config)
        {            

            SL_START_CH1.Minimum = config.Min;
            SL_START_CH1.Maximum = config.Max;
            SL_START_CH1.Value = config.Start[0];
            TB_CH1_MIN.Text = config.Min.ToString();           

            SL_STOP_CH1.Minimum = config.Min;
            SL_STOP_CH1.Maximum = config.Max;
            SL_STOP_CH1.Value = config.Stop[0];
            TB_CH1_MAX.Text = config.Max.ToString();           
                   
            
            SL_START_CH2.Minimum = config.Min;
            SL_START_CH2.Maximum = config.Max;
            SL_START_CH2.Value = config.Start[1];
            TB_CH2_MIN.Text = config.Min.ToString();

            SL_STOP_CH2.Minimum = config.Min;
            SL_STOP_CH2.Maximum = config.Max;
            SL_STOP_CH2.Value = config.Stop[1];
            TB_CH2_MAX.Text = config.Max.ToString();

                        
            SL_START_CH3.Minimum = config.Min;
            SL_START_CH3.Maximum = config.Max;
            SL_START_CH3.Value = config.Start[2];
            TB_CH3_MIN.Text = config.Min.ToString();

            SL_STOP_CH3.Minimum = config.Min;
            SL_STOP_CH3.Maximum = config.Max;
            SL_STOP_CH3.Value = config.Stop[2];
            TB_CH3_MAX.Text = config.Max.ToString();

            
            SL_START_CH4.Minimum = config.Min;
            SL_START_CH4.Maximum = config.Max;
            SL_START_CH4.Value = config.Start[3];
            TB_CH4_MIN.Text = config.Min.ToString();

            SL_STOP_CH4.Minimum = config.Min;
            SL_STOP_CH4.Maximum = config.Max;
            SL_STOP_CH4.Value = config.Stop[3];
            TB_CH4_MAX.Text = config.Max.ToString();
            

            SL_START_CH5.Minimum = config.Min;
            SL_START_CH5.Maximum = config.Max;
            SL_START_CH5.Value = config.Start[4];
            TB_CH5_MIN.Text = config.Min.ToString();

            SL_STOP_CH5.Minimum = config.Min;
            SL_STOP_CH5.Maximum = config.Max;
            SL_STOP_CH5.Value = config.Stop[4];
            TB_CH5_MAX.Text = config.Max.ToString();
            

            SL_START_CH6.Minimum = config.Min;
            SL_START_CH6.Maximum = config.Max;
            SL_START_CH6.Value = config.Start[5];
            TB_CH6_MIN.Text = config.Min.ToString();

            SL_STOP_CH6.Minimum = config.Min;
            SL_STOP_CH6.Maximum = config.Max;
            SL_STOP_CH6.Value = config.Stop[5];
            TB_CH6_MAX.Text = config.Max.ToString();


            SL_START_CH7.Minimum = config.Min;
            SL_START_CH7.Maximum = config.Max;
            SL_START_CH7.Value = config.Start[6];
            TB_CH7_MIN.Text = config.Min.ToString();

            SL_STOP_CH7.Minimum = config.Min;
            SL_STOP_CH7.Maximum = config.Max;
            SL_STOP_CH7.Value = config.Stop[6];
            TB_CH7_MAX.Text = config.Max.ToString();


            SL_START_CH8.Minimum = config.Min;
            SL_START_CH8.Maximum = config.Max;
            SL_START_CH8.Value = config.Start[7];
            TB_CH8_MIN.Text = config.Min.ToString();

            SL_STOP_CH8.Minimum = config.Min;
            SL_STOP_CH8.Maximum = config.Max;
            SL_STOP_CH8.Value = config.Stop[7];
            TB_CH8_MAX.Text = config.Max.ToString();

            

            SL_START_CH1_Scroll(this, new EventArgs());
            SL_START_CH2_Scroll(this, new EventArgs());
            SL_START_CH3_Scroll(this, new EventArgs());
            SL_START_CH4_Scroll(this, new EventArgs());
            SL_START_CH5_Scroll(this, new EventArgs());
            SL_START_CH6_Scroll(this, new EventArgs());
            SL_START_CH7_Scroll(this, new EventArgs());
            SL_START_CH8_Scroll(this, new EventArgs());
            
        }

        

        private void RB_Control_CrankAngle_CheckedChanged(object sender, EventArgs e)
        {
            
            if (RB_Control_CrankAngle.Checked)
            {
                updateAlgorithmTab(imusef_config.CrankAngle_ControllerConfig);
            }
            else if (RB_Control_KneeAngle.Checked)
            {
                updateAlgorithmTab(imusef_config.KneeAngle_ControllerConfig);
            }
            else if (RB_Control_ThighAngle.Checked)
            {
                updateAlgorithmTab(imusef_config.ThighAngle_ControllerConfig);
            }
            else if (RB_Control_Observer.Checked)
            {
                updateAlgorithmTab(imusef_config.Observer_ControllerConfig);
            }
            else if (RB_Control_Biodex.Checked)
            {
                updateAlgorithmTab(imusef_config.Biodex_ControllerConfig);
            }

        }

        private void RB_Control_ThighAngle_CheckedChanged(object sender, EventArgs e)
        {
            RB_Control_CrankAngle_CheckedChanged(sender, e);
        }

        private void RB_Control_KneeAngle_CheckedChanged(object sender, EventArgs e)
        {
            RB_Control_CrankAngle_CheckedChanged(sender, e);
        }

        private void RB_Control_Observer_CheckedChanged(object sender, EventArgs e)
        {
            RB_Control_CrankAngle_CheckedChanged(sender, e);
        }

        private void RB_BiodexController_CheckedChanged(object sender, EventArgs e)
        {
            RB_Control_CrankAngle_CheckedChanged(sender, e);
        }


        private void BT_SaveChanges_Click(object sender, EventArgs e)
        {
            SaveFile(FilePath);
        }


        private void BT_Load_ControllerConfig_Click(object sender, EventArgs e)
        {
            tcpClient.sendMessage(CMD_GET_CONTROLLER_PARAMS + "@");
        }

        private void BT_Update_ControllerConfig_Click(object sender, EventArgs e)
        {

            String JSON = JsonConvert.SerializeObject(imusef_config);

            tcpClient.sendMessage(CMD_SET_CONTROLLER_PARAMS + "@" + JSON);
        }

        private void CB_ShowIndicators_CheckedChanged(object sender, EventArgs e)
        {
            if (CB_ShowIndicators.Checked)
            {
                PB_Indicator_LEFT.Visible = true;
                PB_Indicator_RIGHT.Visible = true;
            }
            else
            {
                PB_Indicator_LEFT.Visible = false;
                PB_Indicator_RIGHT.Visible = false;
            }
        }

        private void CB_Show_Channel_Activity_CheckedChanged(object sender, EventArgs e)
        {
            if (CB_Show_Channel_Activity.Checked)
            {
                PB_LED_CH1_active.Visible = true;
                PB_LED_CH2_active.Visible = true;
                PB_LED_CH3_active.Visible = true;
                PB_LED_CH4_active.Visible = true;
                PB_LED_CH5_active.Visible = true;
                PB_LED_CH6_active.Visible = true;
                PB_LED_CH7_active.Visible = true;
                PB_LED_CH8_active.Visible = true;
            }
            else
            {
                PB_LED_CH1_active.Visible = false;
                PB_LED_CH2_active.Visible = false;
                PB_LED_CH3_active.Visible = false;
                PB_LED_CH4_active.Visible = false;
                PB_LED_CH5_active.Visible = false;
                PB_LED_CH6_active.Visible = false;
                PB_LED_CH7_active.Visible = false;
                PB_LED_CH8_active.Visible = false;
            }
        }


        private void sendSettings()
        {

            TCP_Message_Settings msg = new TCP_Message_Settings();

            int idx = CMB_Controller.SelectedIndex;

            if (idx == 0)
            {
                msg.Controller = IMUSEF_ControllerConfig.CONTROLLER_TCP;
            }
            else if (idx == 1)
            {
                msg.Controller = IMUSEF_ControllerConfig.CONTROLLER_CRANKANGLE;
            }
            else if (idx == 2)
            {
                msg.Controller = IMUSEF_ControllerConfig.CONTROLLER_THIGHANGLE;
            }
            else if (idx == 3)
            {
                msg.Controller = IMUSEF_ControllerConfig.CONTROLLER_KNEEANGLE;
            }           
            else if (idx == 4)
            {
                msg.Controller = IMUSEF_ControllerConfig.CONTROLLER_OBSERVER;
            }
            else if (idx == 5)
            {
                msg.Controller = IMUSEF_ControllerConfig.CONTROLLER_BIODEX;
            }

            msg.Simulated_Cadence = Int32.Parse(TB_Simulation_RPM.Text);
            msg.Simulate_CrankAngle = CB_Simulate_CrankAngle.Checked;
            msg.Simulate_KneeAngles = CB_Simulate_KneeAngles.Checked;
            msg.Simulate_ThighAngles = CB_Simulate_ThighAngles.Checked;

            // Buttons
            msg.FLAG_Button_Emergency = CB_Activate_Button_Emergency.Checked;
            msg.FLAG_Button_Left = CB_Activate_Button_Left.Checked;
            msg.FLAG_Button_Right = CB_Activate_Button_Right.Checked;
            msg.FLAG_Button_Boost = CB_Activate_Button_Boost.Checked;
            msg.FLAG_Switch_Man_Auto = CB_Activate_Switch_Man_Auto.Checked;

            // Modules 
            msg.FLAG_Module_RelayBox = CB_Module_Relaybox.Checked;
            msg.FLAG_Module_Stimulator = CB_Module_Stimulator.Checked;
            msg.FLAG_Module_CrankAngle_Sensor_OpenDAQ = CB_Module_CrankSensor_OpenDAQ.Checked;
            msg.FLAG_Module_CrankAngle_Sensor_IMU_FOX = CB_Module_CrankSensor_IMU_Fox.Checked;
            msg.FLAG_Module_IMUs = CB_Module_IMUs.Checked;
            msg.FLAG_Module_Heartrate_Monitor = CB_Module_Heartrate_Monitor.Checked;
            msg.FLAG_Module_PowerMeter_Rotor = CB_Module_PowerMeter_Rotor.Checked;
            msg.FLAG_Module_HomeTrainer = CB_Module_HomeTrainer.Checked;


            // General Settings
            msg.Max_Manual_Cadence = Int32.Parse(TB_Max_Manual_Cadence.Text);
            msg.MAC_Stimulator = TB_MAC_Stimulator.Text;
            msg.ID_ROTOR = Int32.Parse(TB_ID_ROTOR.Text);
            msg.ID_HeartRateMonitor = Int32.Parse(TB_ID_HeartRateMonitor.Text);

            if (CMB_RearWheel.SelectedIndex == 0)
            {
                msg.WheelCircumference = WHEEL_CAT_TRIKE;
            }
            else if (CMB_RearWheel.SelectedIndex == 1)
            {
                msg.WheelCircumference = WHEEL_ICE_TRIKE_BIG;
            }
            else if (CMB_RearWheel.SelectedIndex == 2)
            {
                msg.WheelCircumference = WHEEL_ICE_TRIKE_SMALL;
            }
            else
            {
                msg.WheelCircumference = WHEEL_CAT_TRIKE;
            }























            String JSON = JsonConvert.SerializeObject(msg);
            tcpClient.sendMessage(CMD_SET_SETTINGS + "@" + JSON);
        }

        private void CB_Simulate_CrankAngle_CheckedChanged(object sender, EventArgs e)
        {
            if (CB_Simulate_CrankAngle.Enabled)
            {
                sendSettings();
            }
        }

        private void CB_Simulate_ThighAngles_CheckedChanged(object sender, EventArgs e)
        {
            if (CB_Simulate_ThighAngles.Enabled)
            {
                sendSettings();
            }
        }

        private void CB_Simulate_KneeAngles_CheckedChanged(object sender, EventArgs e)
        {
            if (CB_Simulate_KneeAngles.Enabled)
            {
                sendSettings();
            }
        }

        private void BT_UpdateCadence_Click(object sender, EventArgs e)
        {
            if (BT_UpdateCadence.Enabled)
            {
                sendSettings();
            }
        }

        private void BT_Calibrate_Click(object sender, EventArgs e)
        {
            tcpClient.sendMessage(CMD_CALIBRATE_SYSTEM + "@");
        }

        private void BT_Stop_IMUSEF_Click(object sender, EventArgs e)
        {
            tcpClient.sendMessage(CMD_STOP_SYSTEM + "@");
        }


        public static bool ping(string IPAddress)
        {
            bool pingable = false;
            Ping pinger = null;

            try
            {
                pinger = new Ping();
                PingReply reply = pinger.Send(IPAddress);
                pingable = reply.Status == IPStatus.Success;
            }
            catch (PingException)
            {
                // Discard PingExceptions and return false;
            }
            finally
            {
                if (pinger != null)
                {
                    pinger.Dispose();
                }
            }

            return pingable;
        }

        private void BT_Start_IMUSEF_Click(object sender, EventArgs e)
        {

            if (PING == false)
            {
                MessageBox.Show("Raspberry is not reachable at the moment!");
                return;
            }

            sshclient = new SshClient(SSH_IP, SSH_User, SSH_Password);
            sshclient.Connect();

            startIMUSEFTHREAD = new Thread(new ThreadStart(startIMUSEF));
            startIMUSEFTHREAD.Start();

            Thread.Sleep(3000);
            
            startIMUSEFTHREAD.Abort();

            if (sshclient != null)
            {
                sshclient.Disconnect();
                sshclient.Dispose();
            }
        }

        private void startIMUSEF()
        {   
                            
            if (sshclient.IsConnected)
            {
                sshclient.RunCommand("screen -dm bash -c 'cd /home/pi/Projects/IMUSEF; python watchdog_IMUSEF.py'");
            }//"cd Projects/IMUSEF; python IMUSEF.py &"


        }


        private void BT_Kill_Imusef_Click(object sender, EventArgs e)
        {
            if (PING == false)
            {
                MessageBox.Show("Raspberry is not reachable at the moment!");
                return;
            }

            SshClient sshcl = new SshClient(SSH_IP, SSH_User, SSH_Password);
            sshcl.Connect();

            if (sshcl.IsConnected)
            {
                sshcl.RunCommand("sudo pkill screen");//"sudo pkill python"
                sshcl.Disconnect();
            }

            sshcl.Dispose();
        }

        private void BT_ShutDown_Click(object sender, EventArgs e)
        {
            if (PING == false)
            {
                MessageBox.Show("Raspberry is not reachable at the moment!");
                return;
            }

            DialogResult dialogResult = MessageBox.Show("Are you sure you would like to shutdown the Raspberry?", "Shut down Raspberry", MessageBoxButtons.YesNo);
            if (dialogResult == DialogResult.Yes)
            {
                try
                {                    

                    SshClient sshcl = new SshClient(SSH_IP, SSH_User, SSH_Password);
                    sshcl.Connect();

                    if (sshcl.IsConnected)
                    {
                        sshcl.RunCommand("sudo poweroff");
                        sshcl.Disconnect();
                    }

                    sshcl.Dispose();
                }
                catch (Exception ex) { }
            }
            
        }

        private void BT_Restart_Raspberry_Click(object sender, EventArgs e)
        {
            if (PING == false)
            {
                MessageBox.Show("Raspberry is not reachable at the moment!");
                return;
            }

            DialogResult dialogResult = MessageBox.Show("Are you sure you would like to restart the Raspberry?", "Shut down Raspberry", MessageBoxButtons.YesNo);
            if (dialogResult == DialogResult.Yes)
            {
                try
                {

                    SshClient sshcl = new SshClient(SSH_IP, SSH_User, SSH_Password);
                    sshcl.Connect();

                    if (sshcl.IsConnected)
                    {
                        sshcl.RunCommand("sudo reboot");
                        sshcl.Disconnect();
                    }

                    sshcl.Dispose();
                }
                catch (Exception ex) { }
            }
        }


        private void BT_StartStop_Logging_Click(object sender, EventArgs e)
        {
            if (BT_StartStop_Logging.Text.Equals("Start"))
            {
                string filename = TB_Filename_Recording.Text;               

                TCP_Message_Recording msg = new TCP_Message_Recording();

                msg.TimeStamp = (long)(DateTime.Now.Subtract(new DateTime(1970, 1, 1))).TotalSeconds;
                msg.Directory = "";
                msg.Filename = "";
                msg.Extension = "";


                if (!filename.Equals(""))
                {
                    if (filename[0].Equals('/'))
                    {
                        filename = filename.Remove(0, 1);
                    }

                    filename = filename.Replace(" ", "_");
                    
                
                    string[] splits = filename.Split('/');

                    

                    if (splits.Length == 1)
                    {
                        filename = splits[0];
                    }
                    else if (splits.Length == 2)
                    {
                        msg.Directory = splits[0];
                        filename = splits[1];
                    }
                    else
                    {
                        MessageBox.Show("Sorry - only one level of Directory is supported. Please remove additional </> signs from the Filename!");
                        return;
                    }

                   
                   splits = filename.Split('.');

                    if (splits.Length == 1)
                    {
                        msg.Filename = splits[0];
                    }
                    else if (splits.Length == 2)
                    {
                        msg.Filename = splits[0];
                        msg.Extension = splits[1];
                    }
                    else
                    {
                        MessageBox.Show("Sorry - The extension choosen is unclear. Only use one <.> between your Filename and Extension!");
                        return;
                    }
                }


                String JSON = JsonConvert.SerializeObject(msg);

                tcpClient.sendMessage(CMD_START_RECORD + "@" + JSON);

                BT_StartStop_Logging.Enabled = false;
                TB_Filename_Recording.Enabled = false;
                TB_Comment.Enabled = false;
                BT_Add_Comment.Enabled = false;

                Thread.Sleep(500);
            }
            else if (BT_StartStop_Logging.Text.Equals("Stop"))
            {
                string filename = TB_Filename_Recording.Text;

                BT_StartStop_Logging.Enabled = false;
                TB_Filename_Recording.Enabled = false;
                TB_Comment.Enabled = false;
                BT_Add_Comment.Enabled = false;


                tcpClient.sendMessage(CMD_STOP_RECORD + "@");

                Thread.Sleep(500);
            }
        }

       

        private void BT_Increase10mA_Click(object sender, EventArgs e)
        {
            UpdateAmplitude(SL_TestStim_Percentage.Value + 10);

        }

        private void BT_Decrease10mA_Click(object sender, EventArgs e)
        {            
            UpdateAmplitude(SL_TestStim_Percentage.Value - 10);
        }

        private void UpdateAmplitude(int intensity)
        {
            if (intensity < 0)
            {
                intensity = 0;
            }
            else if (intensity > 100)
            {
                intensity = 100;
            }

            tcpClient.sendMessage(CMD_SET_STIMULATION_INTENSITY + "@" + intensity);
        }



        private void LBL_I1_Click(object sender, EventArgs e)
        {

        }

        private void button2_Click_1(object sender, EventArgs e)
        {            
            UpdateAmplitude(SL_TestStim_Percentage.Value - 5);
        }

        private void button4_Click(object sender, EventArgs e)
        {
            UpdateAmplitude(SL_TestStim_Percentage.Value - 1);
        }

        private void button3_Click_1(object sender, EventArgs e)
        {                     
            UpdateAmplitude(SL_TestStim_Percentage.Value + 5);
        }

        private void button5_Click(object sender, EventArgs e)
        {
            UpdateAmplitude(SL_TestStim_Percentage.Value + 1);
        }

        private void button6_Click(object sender, EventArgs e)
        {            
            UpdateAmplitude(0);
        }


        private void BT_Add_Comment_Click(object sender, EventArgs e)
        {
            String comment = TB_Comment.Text.ToString();
            TB_Comment.Text = "";
            tcpClient.sendMessage(CMD_ADD_COMMENT + "@" + comment);
        }


        private void CB_Y1_SelectedIndexChanged(object sender, EventArgs e)
        {
            idx_Y1 = CB_Y1.SelectedIndex;

            // Nothing selected
            if (idx_Y1 == 0)
            {
                PB_Zeroline_Y1.Visible = false;

                Y1_Unit = "";

                Y1_MIN = 0;
                Y1_MAX = 0;

                LBL_Y1_MIN.Text = "-";
                LBL_Y1_MAX.Text = "-";

                updateZeroLine_Y1();
            }

            // Thigh Angles
            else if ((new List<int> { 1, 2}).Contains(idx_Y1))
            {
                PB_Zeroline_Y1.Visible = true;

                Y1_Unit = "°";

                Y1_MIN = -90;
                Y1_MAX = 90;

                LBL_Y1_MIN.Text = Y1_MIN.ToString();
                LBL_Y1_MAX.Text = Y1_MAX.ToString();

                updateZeroLine_Y1();
            }

            // Knee Angles
            else if ((new List<int> { 5, 6 }).Contains(idx_Y1))
            {
                PB_Zeroline_Y1.Visible = true;

                Y1_Unit = "°";

                Y1_MIN = -180;
                Y1_MAX = 180;

                LBL_Y1_MIN.Text = Y1_MIN.ToString();
                LBL_Y1_MAX.Text = Y1_MAX.ToString();

                updateZeroLine_Y1();
            }

            // Normalized Angles
            else if ((new List<int> { 3, 4, 7, 8 }).Contains(idx_Y1))
            {
                PB_Zeroline_Y1.Visible = true;

                Y1_Unit = "°";

                Y1_MIN = 0;
                Y1_MAX = 100;

                LBL_Y1_MIN.Text = Y1_MIN.ToString();
                LBL_Y1_MAX.Text = Y1_MAX.ToString();

                updateZeroLine_Y1();
            }

            // Crank Angles
            else if ((new List<int> { 9, 10, 11}).Contains(idx_Y1))
            {
                PB_Zeroline_Y1.Visible = true;

                Y1_Unit = "°";

                Y1_MIN = 0;
                Y1_MAX = 360;

                LBL_Y1_MIN.Text = Y1_MIN.ToString();
                LBL_Y1_MAX.Text = Y1_MAX.ToString();

                updateZeroLine_Y1();
            }

            // Torque HomeTrainer
            else if (idx_Y1 == 12)
            {
                PB_Zeroline_Y1.Visible = false;

                Y1_Unit = "mNm";

                Y1_MIN = -2000;
                Y1_MAX = 2000;

                LBL_Y1_MIN.Text = Y1_MIN.ToString();
                LBL_Y1_MAX.Text = Y1_MAX.ToString();

                updateZeroLine_Y1();
            }

            // Power
            else if ((new List<int> { 13, 14, 18 }).Contains(idx_Y1))
            {
                PB_Zeroline_Y1.Visible = true;

                Y1_Unit = "W";

                Y1_MIN = -0;
                Y1_MAX = 100;

                LBL_Y1_MIN.Text = Y1_MIN.ToString();
                LBL_Y1_MAX.Text = Y1_MAX.ToString();

                updateZeroLine_Y1();
            }

            // Speed
            else if ((new List<int> { 15, 16}).Contains(idx_Y1))
            {
                PB_Zeroline_Y1.Visible = true;

                Y1_Unit = "km/h";

                Y1_MIN = 0;
                Y1_MAX = 30;

                LBL_Y1_MIN.Text = Y1_MIN.ToString();
                LBL_Y1_MAX.Text = Y1_MAX.ToString();

                updateZeroLine_Y1();
            }

            // Torque
            else if ((new List<int> { 17 }).Contains(idx_Y1))
            {
                PB_Zeroline_Y1.Visible = true;

                Y1_Unit = "Nm";

                Y1_MIN = -20;
                Y1_MAX = 20;

                LBL_Y1_MIN.Text = Y1_MIN.ToString();
                LBL_Y1_MAX.Text = Y1_MAX.ToString();

                updateZeroLine_Y1();
            }

            // LoopTime
            else if ((new List<int> { 19 }).Contains(idx_Y1))
            {
                PB_Zeroline_Y1.Visible = true;

                Y1_Unit = "ms";

                Y1_MIN = 0;
                Y1_MAX = 20;

                LBL_Y1_MIN.Text = Y1_MIN.ToString();
                LBL_Y1_MAX.Text = Y1_MAX.ToString();

                updateZeroLine_Y1();
            }

            // DebugValue
            else if ((new List<int> { 21 }).Contains(idx_Y1))
            {
                PB_Zeroline_Y1.Visible = true;

                Y1_Unit = "";

                Y1_MIN = -100;
                Y1_MAX = 100;

                LBL_Y1_MIN.Text = Y1_MIN.ToString();
                LBL_Y1_MAX.Text = Y1_MAX.ToString();

                updateZeroLine_Y1();
            }
        }

        private void CB_Y2_SelectedIndexChanged(object sender, EventArgs e)
        {

            idx_Y2 = CB_Y2.SelectedIndex;

            // Nothing selected
            if (idx_Y2 == 0)
            {
                PB_Zeroline_Y2.Visible = false;

                Y2_Unit = "";

                Y2_MIN = 0;
                Y2_MAX = 0;

                LBL_Y2_MIN.Text = "-";
                LBL_Y2_MAX.Text = "-";

                updateZeroLine_Y2();
            }

            // Thigh Angles
            else if ((new List<int> { 1, 2 }).Contains(idx_Y2))
            {
                PB_Zeroline_Y2.Visible = true;

                Y2_Unit = "°";

                Y2_MIN = -90;
                Y2_MAX = 90;

                LBL_Y2_MIN.Text = Y2_MIN.ToString();
                LBL_Y2_MAX.Text = Y2_MAX.ToString();

                updateZeroLine_Y2();
            }

            // Knee Angles
            else if ((new List<int> { 5, 6 }).Contains(idx_Y2))
            {
                PB_Zeroline_Y2.Visible = true;

                Y2_Unit = "°";

                Y2_MIN = -180;
                Y2_MAX = 180;

                LBL_Y2_MIN.Text = Y2_MIN.ToString();
                LBL_Y2_MAX.Text = Y2_MAX.ToString();

                updateZeroLine_Y2();
            }

            // Normalized Angles
            else if ((new List<int> { 3, 4, 7, 8 }).Contains(idx_Y2))
            {
                PB_Zeroline_Y2.Visible = true;

                Y2_Unit = "°";

                Y2_MIN = 0;
                Y2_MAX = 100;

                LBL_Y2_MIN.Text = Y2_MIN.ToString();
                LBL_Y2_MAX.Text = Y2_MAX.ToString();

                updateZeroLine_Y2();
            }

            // Crank Angles
            else if ((new List<int> { 9, 10, 11 }).Contains(idx_Y2))
            {
                PB_Zeroline_Y2.Visible = true;

                Y2_Unit = "°";

                Y2_MIN = 0;
                Y2_MAX = 360;

                LBL_Y2_MIN.Text = Y2_MIN.ToString();
                LBL_Y2_MAX.Text = Y2_MAX.ToString();

                updateZeroLine_Y2();
            }

            // Torque HomeTrainer
            else if (idx_Y2 == 12)
            {
                PB_Zeroline_Y2.Visible = false;

                Y2_Unit = "mNm";

                Y2_MIN = -2000;
                Y2_MAX = 2000;

                LBL_Y2_MIN.Text = Y2_MIN.ToString();
                LBL_Y2_MAX.Text = Y2_MAX.ToString();

                updateZeroLine_Y2();
            }

            // Power
            else if ((new List<int> { 13, 14, 18 }).Contains(idx_Y2))
            {
                PB_Zeroline_Y2.Visible = true;

                Y2_Unit = "W";

                Y2_MIN = -50;
                Y2_MAX = 50;

                LBL_Y2_MIN.Text = Y2_MIN.ToString();
                LBL_Y2_MAX.Text = Y2_MAX.ToString();

                updateZeroLine_Y2();
            }

            // Speed
            else if ((new List<int> { 15, 16 }).Contains(idx_Y2))
            {
                PB_Zeroline_Y2.Visible = true;

                Y2_Unit = "km/h";

                Y2_MIN = 0;
                Y2_MAX = 30;

                LBL_Y2_MIN.Text = Y2_MIN.ToString();
                LBL_Y2_MAX.Text = Y2_MAX.ToString();

                updateZeroLine_Y2();
            }

            // Torque
            else if ((new List<int> { 17 }).Contains(idx_Y2))
            {
                PB_Zeroline_Y2.Visible = true;

                Y2_Unit = "Nm";

                Y2_MIN = -0;
                Y2_MAX = 100;

                LBL_Y2_MIN.Text = Y2_MIN.ToString();
                LBL_Y2_MAX.Text = Y2_MAX.ToString();

                updateZeroLine_Y2();
            }

            // LoopTime
            else if ((new List<int> { 19 }).Contains(idx_Y2))
            {
                PB_Zeroline_Y2.Visible = true;

                Y2_Unit = "ms";

                Y2_MIN = 0;
                Y2_MAX = 20;

                LBL_Y2_MIN.Text = Y2_MIN.ToString();
                LBL_Y2_MAX.Text = Y2_MAX.ToString();

                updateZeroLine_Y2();
            }

            // DebugValue
            else if ((new List<int> { 21 }).Contains(idx_Y2))
            {
                PB_Zeroline_Y2.Visible = true;

                Y2_Unit = "";

                Y2_MIN = -100;
                Y2_MAX = 100;

                LBL_Y2_MIN.Text = Y2_MIN.ToString();
                LBL_Y2_MAX.Text = Y2_MAX.ToString();

                updateZeroLine_Y2();
            }
        }

        private void BT_Clear_Y1_Click(object sender, EventArgs e)
        {
            CB_Y1.SelectedIndex = 0;
        }

        private void BT_Clear_Y2_Click(object sender, EventArgs e)
        {
            CB_Y2.SelectedIndex = 0;
        }

        private void CMB_Controller_SelectedIndexChanged(object sender, EventArgs e)
        {
            if (CMB_Controller.Enabled)
            {
                sendSettings();
                activateTCPControllerElements();
            }
        }

        private void BT_Reset_Cycling_Computer_Click(object sender, EventArgs e)
        {
            tcpClient.sendMessage(CMD_RESET_CYCLING_COMPUTER + "@");
        }

        private void BT_Update_Max_Manual_Cadence_Click(object sender, EventArgs e)
        {
            if (BT_Update_Max_Manual_Cadence.Enabled)
            {
                sendSettings();
            }
        }

        private void CB_Activate_Button_Emergency_CheckedChanged(object sender, EventArgs e)
        {
            if (CB_Activate_Button_Emergency.Enabled)
            {
                sendSettings();
            }
        }

        private void CB_Activate_Button_Left_CheckedChanged(object sender, EventArgs e)
        {
            if (CB_Activate_Button_Left.Enabled)
            {
                sendSettings();
            }
        }

        private void CB_Activate_Button_Right_CheckedChanged(object sender, EventArgs e)
        {
            if (CB_Activate_Button_Right.Enabled)
            {
                sendSettings();
            }
        }

        private void CB_Activate_Button_Boost_CheckedChanged(object sender, EventArgs e)
        {
            if (CB_Activate_Button_Boost.Enabled)
            {
                sendSettings();
            }
        }

        private void CB_Activate_Switch_Man_Auto_CheckedChanged(object sender, EventArgs e)
        {
            if (CB_Activate_Switch_Man_Auto.Enabled)
            {
                sendSettings();
            }
        }

        private void CMB_RearWheel_SelectedIndexChanged(object sender, EventArgs e)
        {
            if (CMB_RearWheel.Enabled)
            {
                sendSettings();
            }
        }

        private void CB_Module_Relaybox_CheckedChanged(object sender, EventArgs e)
        {
            if (CB_Module_Relaybox.Enabled)
            {
                sendSettings();
            }
        }

        private void CB_Module_Stimulator_CheckedChanged(object sender, EventArgs e)
        {
            if (CB_Module_Stimulator.Enabled)
            {
                sendSettings();
            }
        }

        private void CB_Module_CrankSensor_OpenDAQ_CheckedChanged(object sender, EventArgs e)
        {
            if (CB_Module_CrankSensor_OpenDAQ.Enabled)
            {
                sendSettings();
            }
        }

        private void CB_Module_CrankSensor_IMU_Fox_CheckedChanged(object sender, EventArgs e)
        {
            if (CB_Module_CrankSensor_IMU_Fox.Enabled)
            {
                sendSettings();
            }
        }

        private void CB_Module_IMUs_CheckedChanged(object sender, EventArgs e)
        {
            if (CB_Module_IMUs.Enabled)
            {
                sendSettings();
            }
        }

        private void CB_Module_Heartrate_Monitor_CheckedChanged(object sender, EventArgs e)
        {
            if (CB_Module_Heartrate_Monitor.Enabled)
            {
                sendSettings();
            }
        }

        private void CB_Module_PowerMeter_Rotor_CheckedChanged(object sender, EventArgs e)
        {
            if (CB_Module_PowerMeter_Rotor.Enabled)
            {
                sendSettings();
            }
        }

        private void CB_Module_HomeTrainer_CheckedChanged(object sender, EventArgs e)
        {
            if (CB_Module_HomeTrainer.Enabled)
            {
                sendSettings();
            }
        }

        private void BT_Restart_Imusef2_Click(object sender, EventArgs e)
        {
            BT_Stop_IMUSEF_Click(sender, e);
        }

        private void BT_Restart_Imusef3_Click(object sender, EventArgs e)
        {

            if (BT_Update_Max_Manual_Cadence.Enabled)
            {
                sendSettings();
            }

            Thread.Sleep(2000);

            BT_Stop_IMUSEF_Click(sender, e);
        }
    }
}
