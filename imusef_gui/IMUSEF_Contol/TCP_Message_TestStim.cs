using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace IMUSEF_Control
{
    public class TCP_Message_TestStim
    {
        public float I_percent { get; set; }
        public Boolean[] CH_Active { get; set; }
        public double Burst_Duration { get; set; }
    }
}
