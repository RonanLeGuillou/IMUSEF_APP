using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace IMUSEF_Control
{
    public class IMUSEF_Config
    {
        // Configuration of the Stimulator
        public IMUSEF_StimConfig StimConfig { get; set; }

        // Configuration for the different Controller available
        public IMUSEF_ControllerConfig Biodex_ControllerConfig { get; set; }
        public IMUSEF_ControllerConfig CrankAngle_ControllerConfig { get; set; }
        public IMUSEF_ControllerConfig KneeAngle_ControllerConfig { get; set; }
        public IMUSEF_ControllerConfig ThighAngle_ControllerConfig { get; set; }
        public IMUSEF_ControllerConfig Observer_ControllerConfig { get; set; }

        public IMUSEF_Config()
        {
            this.StimConfig = new IMUSEF_StimConfig();

            this.Biodex_ControllerConfig = new IMUSEF_ControllerConfig();
            this.Biodex_ControllerConfig.Name = IMUSEF_ControllerConfig.CONTROLLER_BIODEX;
            int min = 25;
            int max = 180;
            this.Biodex_ControllerConfig.Min = min;
            this.Biodex_ControllerConfig.Max = max;
            this.Biodex_ControllerConfig.Start = new int[] { min, min, min, min, min, min, min, min };
            this.Biodex_ControllerConfig.Stop = new int[] { min, min, min, min, min, min, min, min };

            this.CrankAngle_ControllerConfig = new IMUSEF_ControllerConfig();
            this.CrankAngle_ControllerConfig.Name = IMUSEF_ControllerConfig.CONTROLLER_CRANKANGLE;
            this.CrankAngle_ControllerConfig.Min = 0;
            this.CrankAngle_ControllerConfig.Max = 360;
            this.CrankAngle_ControllerConfig.Start = new int[] { 0, 0, 0, 0, 0, 0, 0, 0 };
            this.CrankAngle_ControllerConfig.Stop = new int[] { 0, 0, 0, 0, 0, 0, 0, 0 };


            this.KneeAngle_ControllerConfig = new IMUSEF_ControllerConfig();
            this.KneeAngle_ControllerConfig.Name = IMUSEF_ControllerConfig.CONTROLLER_KNEEANGLE;
            this.KneeAngle_ControllerConfig.Min = 0;
            this.KneeAngle_ControllerConfig.Max = 100;
            this.KneeAngle_ControllerConfig.Start = new int[] { 0, 0, 0, 0, 0, 0, 0, 0 };
            this.KneeAngle_ControllerConfig.Stop = new int[] { 0, 0, 0, 0, 0, 0, 0, 0 };

            this.ThighAngle_ControllerConfig = new IMUSEF_ControllerConfig();
            this.ThighAngle_ControllerConfig.Name = IMUSEF_ControllerConfig.CONTROLLER_THIGHANGLE;
            this.ThighAngle_ControllerConfig.Min = 0;
            this.ThighAngle_ControllerConfig.Max = 100;
            this.ThighAngle_ControllerConfig.Start = new int[] { 0, 0, 0, 0, 0, 0, 0, 0 };
            this.ThighAngle_ControllerConfig.Stop = new int[] { 0, 0, 0, 0, 0, 0, 0, 0 };

            this.Observer_ControllerConfig = new IMUSEF_ControllerConfig();
            this.Observer_ControllerConfig.Name = IMUSEF_ControllerConfig.CONTROLLER_OBSERVER;
            this.Observer_ControllerConfig.Min = 0;
            this.Observer_ControllerConfig.Max = 100;
            this.Observer_ControllerConfig.Start = new int[] { 0, 0, 0, 0, 0, 0, 0, 0 };
            this.Observer_ControllerConfig.Stop = new int[] { 0, 0, 0, 0, 0, 0, 0, 0 };
        }
    }
}
