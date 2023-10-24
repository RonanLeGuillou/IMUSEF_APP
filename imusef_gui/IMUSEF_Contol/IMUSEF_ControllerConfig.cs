using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace IMUSEF_Control
{
    public class IMUSEF_ControllerConfig
    {
        public const String CONTROLLER_CRANKANGLE = "CONTROLLER_CRANKANGLE";
        public const String CONTROLLER_THIGHANGLE = "CONTROLLER_THIGHANGLE";
        public const String CONTROLLER_KNEEANGLE = "CONTROLLER_KNEEANGLE";
        public const String CONTROLLER_OBSERVER = "CONTROLLER_OBSERVER";
        public const String CONTROLLER_TCP = "CONTROLLER_TCP";
        public const String CONTROLLER_BIODEX = "CONTROLLER_BIODEX";
        public const String CONTROLLER_NONE = "CONTROLLER_NONE";


        public String Name { get; set; }

        public int Min { get; set; }
        public int Max { get; set; }

        public int[] Start { get; set; }
        public int[] Stop { get; set; }

        public IMUSEF_ControllerConfig()
        {
            this.Name = "";
            this.Min = 0;
            this.Max = 1;
            this.Start = new int[8];
            this.Stop = new int[8];
        }
    }
}
