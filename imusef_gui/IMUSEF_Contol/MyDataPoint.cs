using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace IMUSEF_Control
{
    /// <summary>
    /// Simple container class representing a datapoint
    /// (c) Dipl.Ing. Martin Schmoll, 2014
    /// Mail: martin.schmoll@meduniwien.ac.at
    /// </summary>
    public class MyDataPoint
    {
        public double X, Y1, Y2;

        public MyDataPoint(double X, double Y1, double Y2)
        {
            this.X = X;
            this.Y1 = Y1;
            this.Y2 = Y2;
        }
    }
}
