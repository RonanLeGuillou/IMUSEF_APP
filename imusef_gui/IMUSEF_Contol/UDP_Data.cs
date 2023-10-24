using Newtonsoft.Json;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.Serialization;
using System.Text;
using System.Threading.Tasks;

namespace IMUSEF_Control
{
    public class UDP_Data
    {
        // TimeStamp
        [JsonProperty("T")]
        public double Timestamp { get; set; }

        // ThighAngle Data
        [JsonProperty("TA1")]
        public double LeftThighAngle { get; set; }
        [JsonProperty("TA2")]
        public double RightThighAngle { get; set; }
        [JsonProperty("TA3")]
        public double LeftThighAngle_normalized { get; set; }
        [JsonProperty("TA4")]
        public double RightThighAngle_normalized { get; set; }
        [JsonProperty("TA5")]
        private String t_ThighAngle_Controller_activeChannels { get; set; }
        public bool[] ThighAngle_Controller_activeChannels { get; set; }

        // KneeAngle Data
        [JsonProperty("KA1")]
        public double LeftKneeAngle { get; set; }
        [JsonProperty("KA2")]
        public double RightKneeAngle { get; set; }
        [JsonProperty("KA3")]
        public double LeftKneeAngle_normalized { get; set; }
        [JsonProperty("KA4")]
        public double RightKneeAngle_normalized { get; set; }
        [JsonProperty("KA5")]
        private String t_KneeAngle_Controller_activeChannels { get; set; }
        public bool[] KneeAngle_Controller_activeChannels { get; set; }


        // CrankAngle Data
        [JsonProperty("CA1")]
        public double CrankAngle_OpenDAQ { get; set; }
        [JsonProperty("CA2")]
        public double CrankAngle_ROTOR { get; set; }
        [JsonProperty("CA3")]
        public double CrankAngle_IMU_FOX { get; set; }
        [JsonProperty("CA4")]
        private String t_CrankAngle_Controller_activeChannels { get; set; }
        public bool[] CrankAngle_Controller_activeChannels { get; set; }

        // Observer Data
        [JsonProperty("OB1")]
        public double ObserverPhase { get; set; }
        [JsonProperty("OB2")]
        private String t_Observer_Controller_activeChannels { get; set; }
        public bool[] Observer_Controller_activeChannels { get; set; }

        // PowerMeter Data
        [JsonProperty("PM1")]
        public double DataRate_F1_PowerMeter { get; set; }
        [JsonProperty("PM2")]
        public double DataRate_F2_PowerMeter { get; set; }
        [JsonProperty("PM3")]
        public double DataRate_F3_PowerMeter { get; set; }
        [JsonProperty("PM4")]
        public double Cadence_PowerMeter { get; set; }
        [JsonProperty("PM5")]
        public double Torque_Total_PowerMeter { get; set; }
        [JsonProperty("PM6")]
        public double Power_Total_PowerMeter { get; set; }
        [JsonProperty("PM7")]
        public double Power_Left_PowerMeter { get; set; }
        [JsonProperty("PM8")]
        public double Power_Right_PowerMeter { get; set; }

        // HeartRate Data
        [JsonProperty("HR")]
        public double HeartRate { get; set; }

        // HomeTrainer Data
        [JsonProperty("HT1")]
        public double Torque_HomeTrainer { get; set; }
        [JsonProperty("HT2")]
        public double Power_HomeTrainer { get; set; }
        [JsonProperty("HT3")]
        public double Power_AVG_HomeTrainer { get; set; }
        [JsonProperty("HT4")]
        public double Speed_HomeTrainer { get; set; }

        // Status Values
        // -2 ... ERROR
        // -1 ... Module not activated
        //  0 ... Module not ready
        //  1 ... Module ready
        [JsonProperty("S1")]
        public int Status_Stimulator { get; set; }
        [JsonProperty("S2")]
        public int Status_IMUs { get; set; }
        [JsonProperty("S3")]
        public int Status_CrankAngle_OpenDAQ { get; set; }
        [JsonProperty("S4")]
        public int Status_HomeTrainer { get; set; }
        [JsonProperty("S5")]
        public int Status_PowerMeter { get; set; }
        [JsonProperty("S6")]
        public int Status_HeartRateMonitor { get; set; }
        [JsonProperty("S7")]
        public int Status_Datalogging { get; set; }
        [JsonProperty("S8")]
        public int Status_CrankAngle_IMU_FOX { get; set; }

        // Button States
        [JsonProperty("B1")]
        public int Button_Emergency { get; set; }
        [JsonProperty("B2")]
        public int Button_LEFT { get; set; }
        [JsonProperty("B3")]
        public int Button_RIGHT { get; set; }
        [JsonProperty("B4")]
        public int Button_BOOST { get; set; }
        [JsonProperty("B5")]
        public int Switch_MAN_AUTO { get; set; }


        // Stimulator Data
        [JsonProperty("ST1")]
        public int StimIntensity { get; set; }

        // Cycling Computer Data
        [JsonProperty("CC1")]
        public double Speed_CyclingComputer { get; set; }
        [JsonProperty("CC2")]
        public double Distance_CyclingComputer { get; set; }
        [JsonProperty("CC3")]
        public double Cadence_CyclingComputer { get; set; }


        // System Data
        [JsonProperty("SY1")]
        public double LoopTime { get; set; }
        [JsonProperty("SY2")]
        public double DebugValue { get; set; }

        // Biodex Data
        [JsonProperty("BD2")]
        public bool[] Biodex_Controller_activeChannels { get; set; }


        [OnDeserialized]
        private void OnDeserialized(StreamingContext context)
        {
            // Parsing
            CrankAngle_Controller_activeChannels = parseChannelString(t_CrankAngle_Controller_activeChannels);
            ThighAngle_Controller_activeChannels = parseChannelString(t_ThighAngle_Controller_activeChannels);
            KneeAngle_Controller_activeChannels = parseChannelString(t_KneeAngle_Controller_activeChannels);
            Observer_Controller_activeChannels = parseChannelString(t_Observer_Controller_activeChannels);

        }

        // Converts a binaray ChannelString into a boolean array
        private bool[] parseChannelString(String ch)
        {
            bool[] result = new bool[8];

            for (int i = 0; i < 8; i++)
            {
                if (ch[i].Equals('1'))
                {
                    result[i] = true;
                }
                else
                {
                    result[i] = false;
                }                
            }

            return result;
        }


        // Initialisation
        public UDP_Data()
        {
            this.DebugValue = 0;
            this.Biodex_Controller_activeChannels = new bool[8];

        }

        

    }
    
}
