using System;
using System.Collections.Generic;
using System.Linq;
using System.Net.Sockets;
using System.Text;
using System.Threading;

namespace IMUSEF_Control
{
    
    class myTCP_Client
    {
        public delegate void ReceivedMessage(string str);
        public delegate void UpdatedState(int state);

        public const int NOT_CONNECTED = -1;
        public const int CONNECTING = 0;
        public const int CONNECTED = 1;

        public event ReceivedMessage ReceiveEvent;
        public event UpdatedState UpdatedStateEvent;

        private Int32 port = 12346;
        private String server = "192.168.4.1";
        private TcpClient client;
        private NetworkStream stream;

        private bool ALIVE = true;

        public int STATE = NOT_CONNECTED;

        private Thread connectionThread;
        private Thread sendingThread;
        private Thread receivingThread;

        private Queue<string> sendingQueue = new Queue<string>();
        private readonly object sendingQueueLock = new object();

        public myTCP_Client(String serverIP, Int32 Port)
        {
            this.server = serverIP;
            this.port = Port;

            

        }

        public void start()
        {
            this.connectionThread = new Thread(new ThreadStart(this.connectionWorker));
            this.connectionThread.Start();
            
        }

        public void stop()
        {
            this.ALIVE = false;

            // Close everything.
            this.stream.Close();
            this.client.Close();
        }

        public void sendMessage(String message)
        {
            lock (sendingQueueLock)
            {
                this.sendingQueue.Enqueue(message);
            }
        }
        
        // Manages the connection
        private void connectionWorker()
        {
            while (this.ALIVE)
            {
                if (this.STATE == NOT_CONNECTED)
                {
                    // Clear up old things
                    if (this.stream != null)
                    {
                        this.stream.Close();
                    }

                    if (this.client != null)
                    {
                        this.client.Close();
                    }

                    if (this.sendingThread != null)
                    {
                        this.sendingThread = null;
                    }

                    if (this.receivingThread != null)
                    {
                        this.receivingThread = null;
                    }


                    // Try to connect
                    this.STATE = CONNECTING;
                    this.UpdatedStateEvent(this.STATE);

                    while (this.ALIVE & this.STATE == CONNECTING)
                    {
                        try
                        {
                            // Console.WriteLine("Waiting for Server...");
                            this.client = new TcpClient(server, port);
                            /*this.client = new TcpClient();
                            var result = this.client.BeginConnect(server, port, null, null);

                            var success = result.AsyncWaitHandle.WaitOne(TimeSpan.FromSeconds(0.5));

                            if (!success)
                            {
                                throw new System.Net.Sockets.SocketException();
                            }*/

                            this.stream = client.GetStream();

                            this.STATE = CONNECTED;
                            this.UpdatedStateEvent(this.STATE);

                            this.sendingThread = new Thread(new ThreadStart(this.sendingWorker));
                            this.sendingThread.Start();

                            this.receivingThread = new Thread(new ThreadStart(this.receivingWorker));
                            this.receivingThread.Start();
                        }
                        catch (Exception e)
                        {
                            // Console.WriteLine("SocketException: {0}", e);
                            this.STATE = CONNECTING;
                            this.UpdatedStateEvent(this.STATE);
                             //Console.WriteLine("Server is not ready yet - please wait!");
                            //Thread.Sleep(100);
                        }
                    }
                }

                Thread.Sleep(100);
            }            
        }

        private void sendingWorker()
        {
            String msg = String.Empty;
            Byte[] data;

            while (this.ALIVE & this.STATE == CONNECTED)
            {
               
                
                lock (sendingQueueLock)
                {
                    // Empty Sending Queue
                    while (this.sendingQueue.Count > 0)
                    {
                        msg = this.sendingQueue.Dequeue();
                        data = System.Text.Encoding.ASCII.GetBytes(msg);
                        this.stream.Write(data, 0, msg.Length);

                        Console.WriteLine("Sent: {0}", msg);
                    }
                }


                Thread.Sleep(100); // [ms]
            }
        }

        private void receivingWorker()
        {
            String msg = String.Empty;
            Byte[] data = new Byte[1024]; ;

            while (this.ALIVE & this.STATE == CONNECTED)
            {
                try
                {
                    // Read the first batch of the TcpServer response bytes.
                    Int32 bytes = stream.Read(data, 0, data.Length);
                    msg = System.Text.Encoding.ASCII.GetString(data, 0, bytes);
                }
                catch (Exception e)
                {
                    // Server closed: Reconnect
                    //msg = "Lost connection to Server: trying to reconnect!";
                    this.STATE = NOT_CONNECTED;
                    this.UpdatedStateEvent(this.STATE);
                }

                if (msg.Equals(""))
                {
                    //msg = "Lost connection to Server: trying to reconnect!";
                    this.STATE = NOT_CONNECTED;
                    this.UpdatedStateEvent(this.STATE);
                }

                this.ReceiveEvent(msg);
                
                //Console.WriteLine("Received: {0}", msg);                
            }
        }


    }
}
