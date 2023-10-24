using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace IMUSEF_Control
{
    public class TCP_Message_Settings
    {
        public String Controller { get; set; }

        public int Simulated_Cadence { get; set; }

        public Boolean Simulate_CrankAngle { get; set; }
        public Boolean Simulate_KneeAngles { get; set; }
        public Boolean Simulate_ThighAngles { get; set; }

        public Boolean DataLogging_Active { get; set; }
        public String DataLogging_FilePath { get; set; }

        public int Biodex_Side { get; set; }

        public bool FLAG_Button_Emergency { get; set; }
        public bool FLAG_Button_Left { get; set; }
        public bool FLAG_Button_Right { get; set; }
        public bool FLAG_Button_Boost { get; set; }
        public bool FLAG_Switch_Man_Auto { get; set; }

        public bool FLAG_Module_RelayBox { get; set; }
        public bool FLAG_Module_Stimulator { get; set; }
        public bool FLAG_Module_CrankAngle_Sensor_OpenDAQ { get; set; }
        public bool FLAG_Module_CrankAngle_Sensor_IMU_FOX { get; set; }
        public bool FLAG_Module_IMUs { get; set; }
        public bool FLAG_Module_Heartrate_Monitor { get; set; }
        public bool FLAG_Module_PowerMeter_Rotor { get; set; }
        public bool FLAG_Module_HomeTrainer { get; set; }

        // General Settings
        public int Max_Manual_Cadence { get; set; }
        public int WheelCircumference { get; set; }
        public String MAC_Stimulator { get; set; }
        public int ID_ROTOR { get; set; }
        public int ID_HeartRateMonitor { get; set; }

    }
}
