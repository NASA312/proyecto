using System;
using System.Drawing;
using System.Drawing.Imaging;
using System.IO;
using System.Net;
using System.Text;
using System.Threading;
using System.Windows.Forms;
using System.Runtime.InteropServices;
using System.Diagnostics;
using DPFP;
using DPFP.Capture;
using DPFP.Processing;
using Newtonsoft.Json;

namespace BiometricServer
{
    internal static class Program
    {
        [STAThread]
        static void Main()
        {
            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);

            // Crear form oculto
            FormServer form = new FormServer();
            form.Opacity = 0;
            form.ShowInTaskbar = false;
            form.WindowState = FormWindowState.Minimized;
            form.Show();
            form.Hide();

            Application.Run(form);
        }
    }

    public class FormServer : Form, DPFP.Capture.EventHandler
    {
        [DllImport("user32.dll")]
        private static extern bool SetForegroundWindow(IntPtr hWnd);

        [DllImport("user32.dll")]
        private static extern IntPtr GetForegroundWindow();

        [DllImport("user32.dll")]
        private static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);

        private const int SW_HIDE = 0;
        private const int SW_SHOWMINNOACTIVE = 7;

        private IntPtr _previousWindow = IntPtr.Zero;
        private Capture _capturer;
        private Enrollment _enroller;
        private HttpListener _httpListener;
        private Thread _serverThread;
        private string _currentPersonaId = "";
        private bool _isCapturing = false;
        private string _capturedImageBase64 = "";
        private string _capturedTemplateBase64 = "";
        private bool _captureCompleted = false;
        private readonly object _lockObj = new object();
        private NotifyIcon _trayIcon;
        private RichTextBox _logBox;
        private DPFP.FeatureSet _capturedFeatureSet = null;

        public FormServer()
        {
            InitializeComponent();
        }

        private void InitializeComponent()
        {
            this.Text = "Servidor Biométrico";
            this.Size = new Size(250, 100);
            this.StartPosition = FormStartPosition.Manual;
            this.Location = new Point(Screen.PrimaryScreen.WorkingArea.Right - 260, 10);
            this.FormBorderStyle = FormBorderStyle.None;
            this.ShowInTaskbar = false;
            this.Opacity = 0.0;
            this.TopMost = true;
            this.BackColor = Color.FromArgb(40, 40, 40);

            Label lblEstado = new Label
            {
                Dock = DockStyle.Fill,
                Text = "Esperando...",
                ForeColor = Color.LimeGreen,
                Font = new Font("Segoe UI", 10F, FontStyle.Bold),
                TextAlign = ContentAlignment.MiddleCenter
            };
            this.Controls.Add(lblEstado);

            _logBox = new RichTextBox();
            _logBox.Visible = false;
            this.Controls.Add(_logBox);

            _trayIcon = new NotifyIcon();
            _trayIcon.Icon = SystemIcons.Shield;
            _trayIcon.Text = "Servidor Biométrico Activo";
            _trayIcon.Visible = true;

            ContextMenuStrip menu = new ContextMenuStrip();
            menu.Items.Add("📋 Ver Logs", null, (s, e) => MostrarLogs());
            menu.Items.Add("🔄 Reiniciar Lector", null, (s, e) => ReiniciarLector());
            menu.Items.Add("-");
            menu.Items.Add("❌ Salir", null, (s, e) => CerrarAplicacion());
            _trayIcon.ContextMenuStrip = menu;

            this.Load += FormServer_Load;
            this.FormClosing += FormServer_FormClosing;
        }

        private void FormServer_Load(object sender, EventArgs e)
        {
            LogInterno("═══════════════════════════════════════════════════");
            LogInterno("    SERVIDOR BIOMÉTRICO INICIADO");
            LogInterno("═══════════════════════════════════════════════════");

            this.Show();
            this.Opacity = 0.0;

            MostrarNotificacion("Servidor Biométrico", "Iniciando servicios...", ToolTipIcon.Info);

            InicializarLector();
            IniciarServidorHTTP();

            MostrarNotificacion("Servidor Listo", "Lector activo en http://localhost:5000", ToolTipIcon.Info);
        }

        private void InicializarLector()
        {
            try
            {
                LogInterno("Inicializando lector de huellas...");

                _enroller = new Enrollment();
                _capturer = new Capture();

                if (_capturer != null)
                {
                    _capturer.EventHandler = this;
                    _capturer.StartCapture();

                    LogInterno("✓ Lector inicializado correctamente");
                    LogInterno("✓ EventHandler registrado");
                }
            }
            catch (Exception ex)
            {
                LogInterno($"✗ Error al inicializar lector: {ex.Message}");
                MostrarNotificacion("Error", "No se pudo inicializar el lector", ToolTipIcon.Error);
            }
        }

        private void ReiniciarLector()
        {
            try
            {
                _capturer?.StopCapture();
                Thread.Sleep(500);
                _capturer = new Capture();
                _capturer.EventHandler = this;
                _capturer.StartCapture();
                LogInterno("✓ Lector reiniciado");
                MostrarNotificacion("Lector Reiniciado", "Lector de huellas reiniciado correctamente", ToolTipIcon.Info);
            }
            catch (Exception ex)
            {
                LogInterno($"✗ Error al reiniciar: {ex.Message}");
                MostrarNotificacion("Error", "Error al reiniciar el lector", ToolTipIcon.Error);
            }
        }

        private void IniciarServidorHTTP()
        {
            try
            {
                _httpListener = new HttpListener();
                _httpListener.Prefixes.Add("http://localhost:5000/");
                _httpListener.Start();

                LogInterno("✓ HTTP Server: http://localhost:5000");

                _serverThread = new Thread(EscucharPeticiones);
                _serverThread.IsBackground = true;
                _serverThread.Start();
            }
            catch (Exception ex)
            {
                LogInterno($"✗ Error al iniciar servidor HTTP: {ex.Message}");
            }
        }

        private void EscucharPeticiones()
        {
            while (_httpListener.IsListening)
            {
                try
                {
                    HttpListenerContext context = _httpListener.GetContext();
                    ThreadPool.QueueUserWorkItem(_ => ProcesarPeticion(context));
                }
                catch { }
            }
        }

        private void ProcesarPeticion(HttpListenerContext context)
        {
            string ruta = context.Request.Url.AbsolutePath;
            string metodo = context.Request.HttpMethod;

            if (ruta == "/capturar" && metodo == "GET")
            {
                string personaId = context.Request.QueryString["persona_id"];
                IniciarCaptura(context, personaId);
            }
            else if (ruta == "/estado" && metodo == "GET")
            {
                ObtenerEstado(context);
            }
            else if (ruta == "/verificar" && metodo == "POST")
            {
                VerificarHuella(context);
            }
            else if (ruta == "/cancelar" && metodo == "POST")
            {
                CancelarCaptura(context);
            }
            else if (ruta == "/test" && metodo == "GET")
            {
                TestLector(context);
            }
            else
            {
                EnviarRespuesta(context, 404, new { error = "Ruta no encontrada" });
            }
        }

        private void VerificarHuella(HttpListenerContext context)
        {
            try
            {
                using (StreamReader reader = new StreamReader(context.Request.InputStream, context.Request.ContentEncoding))
                {
                    string jsonBody = reader.ReadToEnd();
                    dynamic data = JsonConvert.DeserializeObject(jsonBody);

                    string featureSetBase64 = data.feature_set_capturado;
                    var tutoresTemplates = data.tutores;

                    LogInterno($"🔍 VERIFICACIÓN INICIADA");
                    LogInterno($"   Tutores a comparar: {tutoresTemplates.Count}");
                    LogInterno($"   FeatureSet recibido: {featureSetBase64.Length} chars");

                    byte[] featureSetBytes = Convert.FromBase64String(featureSetBase64);
                    DPFP.FeatureSet featureSet = new DPFP.FeatureSet();
                    featureSet.DeSerialize(featureSetBytes);

                    LogInterno($"   FeatureSet deserializado OK");

                    DPFP.Verification.Verification verificador = new DPFP.Verification.Verification();
                    DPFP.Verification.Verification.Result resultado = new DPFP.Verification.Verification.Result();

                    foreach (var tutor in tutoresTemplates)
                    {
                        try
                        {
                            string tutorId = tutor.id.ToString();
                            string templateBase64 = tutor.template.ToString();

                            LogInterno($"   → Comparando con tutor {tutorId}...");

                            byte[] templateBytes = Convert.FromBase64String(templateBase64);
                            DPFP.Template template = new DPFP.Template();
                            template.DeSerialize(templateBytes);

                            LogInterno($"     Template deserializado: {templateBytes.Length} bytes");

                            verificador.Verify(featureSet, template, ref resultado);

                            LogInterno($"     Verified={resultado.Verified}, FARAchieved={resultado.FARAchieved}");

                            if (resultado.Verified)
                            {
                                LogInterno($"");
                                LogInterno($"═══════════════════════════════════════════════════");
                                LogInterno($"✅ ¡COINCIDENCIA ENCONTRADA!");
                                LogInterno($"═══════════════════════════════════════════════════");
                                LogInterno($"   Tutor ID: {tutorId}");
                                LogInterno($"   FAR Achieved: {resultado.FARAchieved}");
                                LogInterno($"═══════════════════════════════════════════════════");
                                LogInterno($"");

                                MostrarNotificacion("✅ Huella Verificada",
                                    $"Tutor identificado: ID {tutorId}",
                                    ToolTipIcon.Info, 3000);

                                EnviarRespuesta(context, 200, new
                                {
                                    success = true,
                                    tutor_id = int.Parse(tutorId),
                                    far_achieved = resultado.FARAchieved,
                                    mensaje = "Huella verificada correctamente"
                                });
                                return;
                            }
                        }
                        catch (Exception ex)
                        {
                            LogInterno($"     ✗ Error comparando tutor {tutor.id}: {ex.Message}");
                        }
                    }

                    LogInterno($"");
                    LogInterno($"❌ NO SE ENCONTRÓ COINCIDENCIA");
                    LogInterno($"   Se compararon {tutoresTemplates.Count} tutores");
                    LogInterno($"");

                    MostrarNotificacion("❌ Huella No Reconocida",
                        "No se encontró coincidencia",
                        ToolTipIcon.Warning, 3000);

                    EnviarRespuesta(context, 200, new
                    {
                        success = false,
                        mensaje = "Huella no reconocida en el sistema"
                    });
                }
            }
            catch (Exception ex)
            {
                LogInterno($"");
                LogInterno($"✗✗✗ ERROR CRÍTICO EN VERIFICACIÓN ✗✗✗");
                LogInterno($"   Mensaje: {ex.Message}");
                LogInterno($"   Stack: {ex.StackTrace}");
                LogInterno($"");

                EnviarRespuesta(context, 500, new
                {
                    success = false,
                    error = ex.Message,
                    stack = ex.StackTrace
                });
            }
        }

        private void TestLector(HttpListenerContext context)
        {
            var info = new
            {
                lector_inicializado = _capturer != null,
                enroller_inicializado = _enroller != null,
                capturando = _isCapturing,
                completado = _captureCompleted,
                timestamp = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss")
            };

            EnviarRespuesta(context, 200, info);
        }

        private void IniciarCaptura(HttpListenerContext context, string personaId)
        {
            if (string.IsNullOrEmpty(personaId))
            {
                EnviarRespuesta(context, 400, new { error = "Falta persona_id" });
                return;
            }

            lock (_lockObj)
            {
                _currentPersonaId = personaId;
                _isCapturing = true;
                _captureCompleted = false;
                _capturedImageBase64 = "";
                _capturedTemplateBase64 = "";
                _capturedFeatureSet = null;
                _enroller.Clear();
            }

            LogInterno($"🟡 CAPTURA INICIADA - Persona ID: {personaId}");
            LogInterno("🖐  Esperando huella dactilar...");

            this.Invoke((MethodInvoker)delegate
            {
                _previousWindow = GetForegroundWindow();
                this.Opacity = 0.95;
                Label lbl = this.Controls[0] as Label;
                if (lbl != null)
                {
                    lbl.Text = $"🖐 Capturando\nPersona: {personaId}\n\nColoque su dedo";
                }
                this.TopMost = true;
                this.Activate();
                SetForegroundWindow(this.Handle);
                LogInterno("⚡ Ventana visible para captura (bug SDK)");
            });

            MostrarNotificacion("Captura Iniciada", $"Coloque su dedo en el lector\nPersona ID: {personaId}", ToolTipIcon.Info, 5000);

            EnviarRespuesta(context, 200, new
            {
                success = true,
                message = "Captura iniciada. Coloque su dedo en el lector.",
                persona_id = personaId
            });
        }

        private void CancelarCaptura(HttpListenerContext context)
        {
            lock (_lockObj)
            {
                _isCapturing = false;
                _captureCompleted = false;
                _enroller.Clear();
            }

            LogInterno("🔴 Captura cancelada");
            EnviarRespuesta(context, 200, new { success = true });
        }

        private void ObtenerEstado(HttpListenerContext context)
        {
            lock (_lockObj)
            {
                var estado = new
                {
                    capturando = _isCapturing,
                    completado = _captureCompleted,
                    persona_id = _currentPersonaId,
                    huella_imagen = _captureCompleted ? _capturedImageBase64 : null,
                    huella_template = _captureCompleted ? _capturedTemplateBase64 : null,
                    huella_featureset = (_captureCompleted && _capturedFeatureSet != null)
                        ? Convert.ToBase64String(_capturedFeatureSet.Bytes)
                        : null
                };

                EnviarRespuesta(context, 200, estado);
            }
        }

        private void EnviarRespuesta(HttpListenerContext context, int statusCode, object data)
        {
            context.Response.StatusCode = statusCode;
            context.Response.ContentType = "application/json";
            context.Response.Headers.Add("Access-Control-Allow-Origin", "*");

            string json = JsonConvert.SerializeObject(data);
            byte[] buffer = Encoding.UTF8.GetBytes(json);

            context.Response.ContentLength64 = buffer.Length;
            context.Response.OutputStream.Write(buffer, 0, buffer.Length);
            context.Response.OutputStream.Close();
        }

        // ═══════════════════════════════════════════════════════
        // EVENTOS DEL LECTOR - AQUÍ ESTÁ LA CORRECCIÓN CLAVE
        // ═══════════════════════════════════════════════════════

        public void OnComplete(object Capture, string ReaderSerialNumber, Sample Sample)
        {
            LogInterno($"📸 OnComplete - isCapturing={_isCapturing}, persona_id={_currentPersonaId}");

            if (!_isCapturing)
            {
                LogInterno("   (Ignorado - no hay sesión activa)");
                return;
            }

            // *** DIFERENCIACIÓN CLAVE: Modo verificación vs. registro ***
            bool esVerificacion = (_currentPersonaId == "verificacion");

            // Extraer características con el DataPurpose correcto
            DataPurpose purpose = esVerificacion ? DataPurpose.Verification : DataPurpose.Enrollment;
            FeatureSet features = ExtractFeatures(Sample, purpose);

            if (features == null)
            {
                LogInterno("⚠ Calidad insuficiente");
                return;
            }

            // *** MODO VERIFICACIÓN: Captura única ***
            if (esVerificacion)
            {
                LogInterno("🔍 Modo verificación - captura única");

                _capturedFeatureSet = features;

                lock (_lockObj)
                {
                    _captureCompleted = true;
                    _isCapturing = false;
                }

                LogInterno("✅ FeatureSet capturado para verificación");

                this.Invoke((MethodInvoker)delegate
                {
                    this.Opacity = 0.0;
                    if (_previousWindow != IntPtr.Zero)
                    {
                        SetForegroundWindow(_previousWindow);
                    }
                });

                MostrarNotificacion("Huella Capturada",
                    "Verificando...",
                    ToolTipIcon.Info, 2000);

                return;
            }

            // *** MODO REGISTRO: Proceso de enrollment completo ***
            try
            {
                _enroller.AddFeatures(features);

                if (_enroller.FeaturesNeeded > 0)
                {
                    LogInterno($"⏳ Faltan {_enroller.FeaturesNeeded} muestras");
                    MostrarNotificacion("Procesando",
                        $"Faltan {_enroller.FeaturesNeeded} muestras\nLevante y vuelva a colocar",
                        ToolTipIcon.Warning, 2000);
                }

                if (_enroller.TemplateStatus == Enrollment.Status.Ready)
                {
                    Bitmap bitmap = ConvertSampleToBitmap(Sample);
                    _capturedImageBase64 = BitmapToBase64(bitmap);

                    DPFP.Template template = _enroller.Template;
                    _capturedTemplateBase64 = Convert.ToBase64String(template.Bytes);
                    _capturedFeatureSet = features;

                    lock (_lockObj)
                    {
                        _captureCompleted = true;
                        _isCapturing = false;
                    }

                    LogInterno("✅ CAPTURA COMPLETADA (Registro)");
                    LogInterno($"   Persona ID: {_currentPersonaId}");
                    LogInterno($"   Template: {_capturedTemplateBase64.Length} chars");

                    MostrarNotificacion("¡Captura Exitosa!",
                        $"Huella registrada correctamente\nPersona ID: {_currentPersonaId}",
                        ToolTipIcon.Info, 3000);

                    this.Invoke((MethodInvoker)delegate
                    {
                        this.Opacity = 0.0;
                        Label lbl = this.Controls[0] as Label;
                        if (lbl != null)
                        {
                            lbl.Text = "Esperando...";
                        }

                        if (_previousWindow != IntPtr.Zero)
                        {
                            SetForegroundWindow(_previousWindow);
                        }
                    });

                    _enroller.Clear();
                }
            }
            catch (Exception ex)
            {
                LogInterno($"✗ Error: {ex.Message}");
            }
        }

        public void OnFingerGone(object Capture, string ReaderSerialNumber)
        {
            if (_isCapturing)
            {
                LogInterno("👆 Dedo retirado");
            }
        }

        public void OnFingerTouch(object Capture, string ReaderSerialNumber)
        {
            if (_isCapturing)
            {
                LogInterno("👇 Dedo detectado");
            }
        }

        public void OnReaderConnect(object Capture, string ReaderSerialNumber)
        {
            LogInterno($"✓ Lector conectado: {ReaderSerialNumber}");
        }

        public void OnReaderDisconnect(object Capture, string ReaderSerialNumber)
        {
            LogInterno($"✗ Lector desconectado: {ReaderSerialNumber}");
        }

        public void OnSampleQuality(object Capture, string ReaderSerialNumber, CaptureFeedback CaptureFeedback)
        {
            // Silencioso
        }

        // ═══════════════════════════════════════════════════════
        // MÉTODOS AUXILIARES
        // ═══════════════════════════════════════════════════════

        private FeatureSet ExtractFeatures(Sample sample, DataPurpose purpose)
        {
            FeatureExtraction extractor = new FeatureExtraction();
            CaptureFeedback feedback = CaptureFeedback.None;
            FeatureSet features = new FeatureSet();

            extractor.CreateFeatureSet(sample, purpose, ref feedback, ref features);

            LogInterno($"   Feedback: {feedback}");

            return (feedback == CaptureFeedback.Good) ? features : null;
        }

        private Bitmap ConvertSampleToBitmap(Sample sample)
        {
            SampleConversion converter = new SampleConversion();
            Bitmap bitmap = null;
            converter.ConvertToPicture(sample, ref bitmap);
            return bitmap;
        }

        private string BitmapToBase64(Bitmap bitmap)
        {
            using (MemoryStream ms = new MemoryStream())
            {
                bitmap.Save(ms, ImageFormat.Png);
                return Convert.ToBase64String(ms.ToArray());
            }
        }

        private void LogInterno(string mensaje)
        {
            if (_logBox.InvokeRequired)
            {
                _logBox.Invoke((MethodInvoker)delegate { LogInterno(mensaje); });
                return;
            }

            string timestamp = DateTime.Now.ToString("HH:mm:ss");
            _logBox.AppendText($"[{timestamp}] {mensaje}\n");

            try
            {
                string logFile = Path.Combine(Application.StartupPath, "biometric.log");
                File.AppendAllText(logFile, $"[{timestamp}] {mensaje}\n");
            }
            catch { }
        }

        private void MostrarNotificacion(string titulo, string mensaje, ToolTipIcon icon = ToolTipIcon.Info, int duracion = 3000)
        {
            if (this.InvokeRequired)
            {
                this.Invoke((MethodInvoker)delegate { MostrarNotificacion(titulo, mensaje, icon, duracion); });
                return;
            }

            _trayIcon.ShowBalloonTip(duracion, titulo, mensaje, icon);
        }

        private void MostrarLogs()
        {
            Form logForm = new Form
            {
                Text = "Logs del Servidor Biométrico",
                Size = new Size(800, 600),
                StartPosition = FormStartPosition.CenterScreen
            };

            RichTextBox logView = new RichTextBox
            {
                Dock = DockStyle.Fill,
                Font = new Font("Consolas", 9F),
                BackColor = Color.Black,
                ForeColor = Color.LimeGreen,
                ReadOnly = true,
                Text = _logBox.Text
            };

            logForm.Controls.Add(logView);
            logForm.Show();
        }

        private void CerrarAplicacion()
        {
            DialogResult result = MessageBox.Show(
                "¿Cerrar el servidor biométrico?\n\nLa aplicación web no podrá capturar huellas.",
                "Confirmar Cierre",
                MessageBoxButtons.YesNo,
                MessageBoxIcon.Question);

            if (result == DialogResult.Yes)
            {
                _trayIcon.Visible = false;
                Application.Exit();
            }
        }

        private void FormServer_FormClosing(object sender, FormClosingEventArgs e)
        {
            _httpListener?.Stop();
            _capturer?.StopCapture();
            _trayIcon.Visible = false;
        }
    }
}