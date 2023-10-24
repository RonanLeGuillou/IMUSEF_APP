using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace IMUSEF_Control
{
    public class IMUSEF_StimConfig
    {
        public double F { get; set; }
        public double F_Boost { get; set; }

        public int[] I_Max { get; set; }
        public bool[] Monophasic { get; set; }
        public int[] PhW { get; set; }
        public int[] PhW_Boost { get; set; }
        public int[] IPG { get; set; }

        public int[] RampUP { get; set; }
        public int[] RampDOWN { get; set; }





        public IMUSEF_StimConfig()
        {
            this.F = 0;
            this.F_Boost = 0;

            this.I_Max = new int[8];
            this.Monophasic = new bool[8];
            this.PhW = new int[8];
            this.PhW_Boost = new int[8];
            this.IPG = new int[8];
            this.RampUP = new int[8];
            this.RampDOWN = new int[8];            
        }
    }
}
