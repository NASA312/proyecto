using DPFP;
using DPFP.Capture;
using DPFP.Processing;
using Newtonsoft.Json;
using System;
using System.Collections.Generic;
using System.Drawing;
using System.Drawing.Imaging;
using System.IO;
using System.Net;
using System.Runtime.InteropServices;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using System.Windows.Forms;
// NOTA: NO se importa "using DPFP.Capture" porque genera ambigüedad
// con System.Text.RegularExpressions.Capture. Se usa nombre completo.

namespace BiometricServer
{
    // ═══════════════════════════════════════════════════════════════════
    //  ENTRY POINT
    // ═══════════════════════════════════════════════════════════════════
    internal static class Program
    {
        [STAThread]
        static void Main()
        {
            Application.EnableVisualStyles();
            Application.SetCompatibleTextRenderingDefault(false);
            Application.Run(new FormServer());
        }
    }

    // ═══════════════════════════════════════════════════════════════════
    //  FORM PRINCIPAL  (completamente invisible para el usuario)
    // ═══════════════════════════════════════════════════════════════════
    public class FormServer : Form, DPFP.Capture.EventHandler
    {
        // ───────────────────────────────────────────────────────────────
        // WIN32 APIs necesarias para dar foco sin mostrar ventana
        // ───────────────────────────────────────────────────────────────

        [DllImport("user32.dll")] private static extern bool SetForegroundWindow(IntPtr hWnd);
        [DllImport("user32.dll")] private static extern IntPtr GetForegroundWindow();
        [DllImport("user32.dll")] private static extern bool ShowWindow(IntPtr hWnd, int nCmdShow);
        [DllImport("user32.dll")] private static extern bool BringWindowToTop(IntPtr hWnd);
        [DllImport("user32.dll")] private static extern int GetWindowThreadProcessId(IntPtr hWnd, out int pid);
        [DllImport("user32.dll")] private static extern bool AttachThreadInput(int idAttach, int idAttachTo, bool fAttach);
        [DllImport("user32.dll")] private static extern int SetWindowLong(IntPtr hWnd, int nIndex, int dwNewLong);
        [DllImport("user32.dll")] private static extern int GetWindowLong(IntPtr hWnd, int nIndex);
        [DllImport("kernel32.dll")] private static extern int GetCurrentThreadId();

        // Constantes Win32
        private const int SW_HIDE = 0;
        private const int SW_SHOWNOACTIVATE = 4;   // muestra la ventana SIN darle foco
        private const int GWL_EXSTYLE = -20;
        private const int WS_EX_TOOLWINDOW = 0x00000080; // ocultar de Alt+Tab
        private const int WS_EX_NOACTIVATE = 0x08000000; // no robar foco al mostrarse

        // ───────────────────────────────────────────────────────────────
        // ESTADO INTERNO
        // ───────────────────────────────────────────────────────────────
        private IntPtr _previousWindow = IntPtr.Zero;
        private DPFP.Capture.Capture _capturer;
        private Enrollment _enroller;
        private HttpListener _httpListener;
        private Thread _serverThread;
        private string _currentPersonaId = "";
        private bool _isCapturing = false;
        private string _capturedImageBase64 = "";
        private string _capturedTemplateBase64 = "";
        private bool _captureCompleted = false;
        private DPFP.FeatureSet _capturedFeatureSet = null;
        private readonly object _lockObj = new object();

        // Controles UI (ocultos)
        private NotifyIcon _trayIcon;
        private RichTextBox _logBox;

        // ═══════════════════════════════════════════════════════════════
        //  OVERRIDE CLAVE: impide que la ventana robe el foco al
        //  mostrarse, incluso cuando llamamos a Show() internamente.
        // ═══════════════════════════════════════════════════════════════
        protected override bool ShowWithoutActivation => true;

        // ═══════════════════════════════════════════════════════════════
        //  CONSTRUCTOR
        // ═══════════════════════════════════════════════════════════════
        public FormServer()
        {
            // Propiedades del Form que lo hacen completamente invisible
            this.Text = "Servidor Biométrico";
            this.Size = new Size(1, 1);
            this.FormBorderStyle = FormBorderStyle.None;
            this.ShowInTaskbar = false;
            this.Opacity = 0.0;
            this.TopMost = false;      // NO TopMost: evita parpadeos
            this.StartPosition = FormStartPosition.Manual;
            this.Location = new Point(-32000, -32000); // fuera de pantalla

            // Log box oculto (solo para guardar logs en archivo)
            _logBox = new RichTextBox { Visible = false, Width = 1, Height = 1 };
            this.Controls.Add(_logBox);

            // Ícono de bandeja del sistema
            _trayIcon = new NotifyIcon();
            _trayIcon.Icon = SystemIcons.Shield;
            _trayIcon.Text = "Servidor Biométrico";

            var menu = new ContextMenuStrip();
            menu.Items.Add("Ver Logs", null, (s, e) => MostrarLogs());
            menu.Items.Add("Reiniciar Lector", null, (s, e) => ReiniciarLector());
            menu.Items.Add("-");
            menu.Items.Add("Salir", null, (s, e) => CerrarApp());
            _trayIcon.ContextMenuStrip = menu;
            _trayIcon.Visible = true;

            this.Load += OnLoad;
            this.FormClosing += OnClosing;
        }

        // ═══════════════════════════════════════════════════════════════
        //  HANDLE CREADO: aplicar estilos Win32 que ocultan la ventana
        //  del sistema (Alt+Tab, barra de tareas, foco automático)
        // ═══════════════════════════════════════════════════════════════
        protected override void OnHandleCreated(EventArgs e)
        {
            base.OnHandleCreated(e);
            int exStyle = GetWindowLong(this.Handle, GWL_EXSTYLE);
            exStyle |= WS_EX_TOOLWINDOW;  // quitar de Alt+Tab
            exStyle |= WS_EX_NOACTIVATE;  // no activar al mostrarse
            SetWindowLong(this.Handle, GWL_EXSTYLE, exStyle);
        }

        // ═══════════════════════════════════════════════════════════════
        //  CARGA INICIAL
        // ═══════════════════════════════════════════════════════════════
        private void OnLoad(object sender, EventArgs e)
        {
            Log("=== SERVIDOR BIOMÉTRICO INICIADO ===");

            // Mostrar ventana en modo "no activo": existe en Windows
            // y puede recibir mensajes, pero NO roba el foco al usuario
            ShowWindow(this.Handle, SW_SHOWNOACTIVATE);
            this.Opacity = 0.0;

            InicializarLector();
            IniciarServidorHTTP();

            Notificar("Servidor Biométrico", "Listo en http://localhost:5000");
        }

        // ═══════════════════════════════════════════════════════════════
        //  LECTOR DE HUELLAS
        // ═══════════════════════════════════════════════════════════════
        private void InicializarLector()
        {
            try
            {
                _enroller = new Enrollment();
                _capturer = new DPFP.Capture.Capture();
                _capturer.EventHandler = this;
                _capturer.StartCapture();
                Log("✓ Lector inicializado");
            }
            catch (Exception ex)
            {
                Log("✗ Error lector: " + ex.Message);
                Notificar("Error", "No se pudo inicializar el lector de huellas");
            }
        }

        private void ReiniciarLector()
        {
            try
            {
                if (_capturer != null) _capturer.StopCapture();
                Thread.Sleep(300);
                _capturer = new DPFP.Capture.Capture();
                _capturer.EventHandler = this;
                _capturer.StartCapture();
                Log("✓ Lector reiniciado");
                Notificar("Lector", "Lector reiniciado correctamente");
            }
            catch (Exception ex)
            {
                Log("✗ Error reiniciando lector: " + ex.Message);
            }
        }

        // ═══════════════════════════════════════════════════════════════
        //  DAR FOCO AL PROCESO SIN MOSTRAR VENTANA
        //
        //  Por qué es necesario:
        //  El SDK de DigitalPersona entrega los eventos de huella
        //  únicamente a la ventana que tiene el foco del sistema.
        //  Si otra ventana (el navegador) tiene el foco, el evento
        //  OnComplete nunca se dispara.
        //
        //  La solución con AttachThreadInput:
        //  1. Obtenemos el thread que actualmente tiene el foco (el navegador)
        //  2. "Adjuntamos" nuestro thread a ese thread temporalmente
        //  3. Esto permite que SetForegroundWindow funcione aunque
        //     nuestra ventana esté en segundo plano
        //  4. Llamamos SetForegroundWindow → nuestro proceso obtiene el foco
        //  5. Desadjuntamos los threads
        //  6. La ventana tiene foco de SISTEMA pero está invisible (opacity=0,
        //     tamaño 1x1, fuera de pantalla) → el usuario no ve nada
        // ═══════════════════════════════════════════════════════════════
        private void DarFocoInvisible()
        {
            if (this.InvokeRequired)
            {
                this.BeginInvoke(new Action(DarFocoInvisible));
                return;
            }

            try
            {
                // Guardar ventana actual para restaurarla después
                _previousWindow = GetForegroundWindow();

                int foregroundThread = GetWindowThreadProcessId(_previousWindow, out int _pid);
                int currentThread = GetCurrentThreadId();

                // Adjuntar threads
                AttachThreadInput(currentThread, foregroundThread, true);

                // Dar foco a nuestra ventana (invisible)
                BringWindowToTop(this.Handle);
                SetForegroundWindow(this.Handle);

                // Desadjuntar threads
                AttachThreadInput(currentThread, foregroundThread, false);

                // Garantizar que sigue siendo invisible
                this.Opacity = 0.0;

                Log("⚡ Foco otorgado al proceso (invisible)");
            }
            catch (Exception ex)
            {
                Log("⚠ Error en DarFocoInvisible: " + ex.Message);
            }
        }

        private void RestaurarFoco()
        {
            if (this.InvokeRequired)
            {
                this.BeginInvoke(new Action(RestaurarFoco));
                return;
            }

            try
            {
                if (_previousWindow != IntPtr.Zero)
                {
                    SetForegroundWindow(_previousWindow);
                    _previousWindow = IntPtr.Zero;
                }
            }
            catch { }
        }

        // ═══════════════════════════════════════════════════════════════
        //  SERVIDOR HTTP
        // ═══════════════════════════════════════════════════════════════
        private void IniciarServidorHTTP()
        {
            try
            {
                _httpListener = new HttpListener();
                _httpListener.Prefixes.Add("http://localhost:5000/");
                _httpListener.Start();

                _serverThread = new Thread(EscucharPeticiones) { IsBackground = true };
                _serverThread.Start();

                Log("✓ HTTP escuchando en http://localhost:5000");
            }
            catch (Exception ex)
            {
                Log("✗ Error HTTP: " + ex.Message);
                Notificar("Error", "No se pudo iniciar el servidor HTTP.\nEjecuta el script de configuración como Administrador.");
            }
        }

        private void EscucharPeticiones()
        {
            while (_httpListener != null && _httpListener.IsListening)
            {
                try
                {
                    var ctx = _httpListener.GetContext();
                    ThreadPool.QueueUserWorkItem(_ => ProcesarPeticion(ctx));
                }
                catch { }
            }
        }

        private void ProcesarPeticion(HttpListenerContext ctx)
        {
            // CORS: necesario para que Django pueda llamar desde el navegador
            ctx.Response.Headers.Add("Access-Control-Allow-Origin", "*");
            ctx.Response.Headers.Add("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
            ctx.Response.Headers.Add("Access-Control-Allow-Headers", "Content-Type");

            if (ctx.Request.HttpMethod == "OPTIONS")
            {
                ctx.Response.StatusCode = 200;
                ctx.Response.OutputStream.Close();
                return;
            }

            string ruta = ctx.Request.Url.AbsolutePath;
            string metodo = ctx.Request.HttpMethod;

            try
            {
                if (ruta == "/capturar" && metodo == "GET") Capturar(ctx);
                else if (ruta == "/estado" && metodo == "GET") Estado(ctx);
                else if (ruta == "/verificar" && metodo == "POST") Verificar(ctx);
                else if (ruta == "/cancelar" && metodo == "POST") Cancelar(ctx);
                else if (ruta == "/test" && metodo == "GET") Test(ctx);
                else Responder(ctx, 404, new { error = "Ruta no encontrada" });
            }
            catch (Exception ex)
            {
                Log("✗ Error procesando petición: " + ex.Message);
                Responder(ctx, 500, new { error = ex.Message });
            }
        }

        // ═══════════════════════════════════════════════════════════════
        //  ENDPOINTS
        // ═══════════════════════════════════════════════════════════════

        // GET /capturar?persona_id=123
        // Django llama esto cuando el usuario hace clic en "Registrar huella"
        private void Capturar(HttpListenerContext ctx)
        {
            string personaId = ctx.Request.QueryString["persona_id"];

            if (string.IsNullOrEmpty(personaId))
            {
                Responder(ctx, 400, new { error = "Falta persona_id" });
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

            Log("► Captura iniciada - Persona ID: " + personaId);

            // DAR FOCO INVISIBLE: el SDK puede detectar huellas
            DarFocoInvisible();

            Notificar("Captura Iniciada", "Coloque el dedo en el lector\nPersona: " + personaId);

            Responder(ctx, 200, new
            {
                success = true,
                message = "Captura iniciada. Coloque el dedo en el lector.",
                persona_id = personaId
            });
        }

        // GET /estado
        // Django hace polling a este endpoint para saber si ya se capturó la huella
        private void Estado(HttpListenerContext ctx)
        {
            lock (_lockObj)
            {
                Responder(ctx, 200, new
                {
                    capturando = _isCapturing,
                    completado = _captureCompleted,
                    persona_id = _currentPersonaId,
                    huella_imagen = _captureCompleted ? _capturedImageBase64 : null,
                    huella_template = _captureCompleted ? _capturedTemplateBase64 : null,
                    huella_featureset = (_captureCompleted && _capturedFeatureSet != null)
                                        ? Convert.ToBase64String(_capturedFeatureSet.Bytes)
                                        : null
                });
            }
        }

        // POST /verificar
        // Django manda el featureset capturado + lista de templates para comparar
        // Se hace en PARALELO para que no tarde aunque haya muchas huellas
        private void Verificar(HttpListenerContext ctx)
        {
            try
            {
                string body;
                using (var r = new StreamReader(ctx.Request.InputStream, ctx.Request.ContentEncoding))
                    body = r.ReadToEnd();

                dynamic data = JsonConvert.DeserializeObject(body);

                string featureSetB64 = (string)data.feature_set_capturado;
                var tutores = data.tutores;

                // Deserializar el featureset capturado
                byte[] fsBytes = Convert.FromBase64String(featureSetB64);
                DPFP.FeatureSet fs = new DPFP.FeatureSet();
                fs.DeSerialize(fsBytes);

                Log("► Verificando contra " + tutores.Count + " tutor(es)...");

                // Convertir a lista para poder usar Parallel.ForEach
                var lista = new List<dynamic>();
                foreach (var t in tutores) lista.Add(t);

                // Variables compartidas entre threads
                string tutorEncontrado = null;
                double farEncontrado = 0;
                object resultLock = new object();

                // Comparación en PARALELO: todos los templates al mismo tiempo
                Parallel.ForEach(
                    lista,
                    new ParallelOptions { MaxDegreeOfParallelism = Environment.ProcessorCount },
                    (tutor, estado) =>
                    {
                        if (estado.ShouldExitCurrentIteration) return;

                        try
                        {
                            string tutorId = tutor.id.ToString();
                            string templateB64 = tutor.template.ToString();

                            byte[] tBytes = Convert.FromBase64String(templateB64);
                            DPFP.Template template = new DPFP.Template();
                            template.DeSerialize(tBytes);

                            // Cada thread necesita su propia instancia de Verification
                            var verificador = new DPFP.Verification.Verification();
                            var resultado = new DPFP.Verification.Verification.Result();

                            verificador.Verify(fs, template, ref resultado);

                            Log("  → Tutor " + tutorId + ": " + resultado.Verified + " (FAR=" + resultado.FARAchieved + ")");

                            if (resultado.Verified)
                            {
                                lock (resultLock)
                                {
                                    if (tutorEncontrado == null)
                                    {
                                        tutorEncontrado = tutorId;
                                        farEncontrado = resultado.FARAchieved;
                                    }
                                }
                                estado.Stop(); // detener los demás threads
                            }
                        }
                        catch (Exception ex)
                        {
                            Log("  ✗ Error con tutor " + tutor.id + ": " + ex.Message);
                        }
                    }
                );

                if (tutorEncontrado != null)
                {
                    Log("✓ COINCIDENCIA: Tutor ID " + tutorEncontrado);
                    Notificar("Huella Verificada", "Tutor identificado: ID " + tutorEncontrado);
                    Responder(ctx, 200, new
                    {
                        success = true,
                        tutor_id = int.Parse(tutorEncontrado),
                        far_achieved = farEncontrado,
                        mensaje = "Huella verificada correctamente"
                    });
                }
                else
                {
                    Log("✗ Sin coincidencia en " + lista.Count + " tutor(es)");
                    Notificar("Huella No Reconocida", "No se encontró coincidencia");
                    Responder(ctx, 200, new
                    {
                        success = false,
                        mensaje = "Huella no reconocida en el sistema"
                    });
                }
            }
            catch (Exception ex)
            {
                Log("✗ ERROR en Verificar: " + ex.Message);
                Responder(ctx, 500, new { success = false, error = ex.Message });
            }
        }

        // POST /cancelar
        private void Cancelar(HttpListenerContext ctx)
        {
            lock (_lockObj)
            {
                _isCapturing = false;
                _captureCompleted = false;
                _enroller.Clear();
            }
            RestaurarFoco();
            Log("■ Captura cancelada");
            Responder(ctx, 200, new { success = true });
        }

        // GET /test
        // Para verificar desde el navegador que el servidor está activo
        private void Test(HttpListenerContext ctx)
        {
            Responder(ctx, 200, new
            {
                success = true,
                lector_inicializado = _capturer != null,
                capturando = _isCapturing,
                completado = _captureCompleted,
                timestamp = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss")
            });
        }

        // ═══════════════════════════════════════════════════════════════
        //  EVENTOS DEL LECTOR (DPFP.Capture.EventHandler)
        // ═══════════════════════════════════════════════════════════════
        public void OnComplete(object Capture, string ReaderSerialNumber, Sample Sample)
        {
            Log("► OnComplete - isCapturing=" + _isCapturing + " persona=" + _currentPersonaId);

            if (!_isCapturing)
            {
                Log("  (ignorado, no hay sesión activa)");
                return;
            }

            // Modo verificación: solo necesita 1 muestra
            bool esVerificacion = (_currentPersonaId == "verificacion");

            DataPurpose purpose = esVerificacion ? DataPurpose.Verification : DataPurpose.Enrollment;
            FeatureSet features = ExtraerCaracteristicas(Sample, purpose);

            if (features == null)
            {
                Log("⚠ Calidad insuficiente, intente de nuevo");
                Notificar("Calidad Insuficiente", "Presione el dedo más firmemente en el lector");
                return;
            }

            // ── MODO VERIFICACIÓN ────────────────────────────────────
            if (esVerificacion)
            {
                _capturedFeatureSet = features;

                lock (_lockObj)
                {
                    _captureCompleted = true;
                    _isCapturing = false;
                }

                RestaurarFoco();
                Notificar("Huella Capturada", "Procesando verificación...");
                Log("✓ FeatureSet capturado para verificación");
                return;
            }

            // ── MODO REGISTRO (enrollment: requiere varias muestras) ──
            try
            {
                _enroller.AddFeatures(features);

                int faltantes = (int)_enroller.FeaturesNeeded; // cast necesario: FeaturesNeeded es uint

                if (faltantes > 0)
                {
                    Log("  Muestras restantes: " + faltantes);
                    Notificar("Procesando", "Faltan " + faltantes + " muestra(s)\nLevante y vuelva a colocar el dedo");
                    return;
                }

                if (_enroller.TemplateStatus == Enrollment.Status.Ready)
                {
                    // Convertir a imagen
                    Bitmap bmp = ConvertirABitmap(Sample);
                    _capturedImageBase64 = (bmp != null) ? BitmapABase64(bmp) : "";
                    bmp?.Dispose();

                    // Obtener template
                    DPFP.Template tpl = _enroller.Template;
                    _capturedTemplateBase64 = Convert.ToBase64String(tpl.Bytes);
                    _capturedFeatureSet = features;

                    lock (_lockObj)
                    {
                        _captureCompleted = true;
                        _isCapturing = false;
                    }

                    Log("✓ REGISTRO COMPLETADO - Persona: " + _currentPersonaId);
                    Notificar("Registro Exitoso", "Huella registrada\nPersona ID: " + _currentPersonaId);

                    RestaurarFoco();
                    _enroller.Clear();
                }
            }
            catch (Exception ex)
            {
                Log("✗ Error en registro: " + ex.Message);
            }
        }

        public void OnFingerGone(object Capture, string ReaderSerialNumber)
        {
            if (_isCapturing) Log("  Dedo retirado");
        }

        public void OnFingerTouch(object Capture, string ReaderSerialNumber)
        {
            if (_isCapturing) Log("  Dedo detectado");
        }

        public void OnReaderConnect(object Capture, string ReaderSerialNumber)
        {
            Log("✓ Lector conectado: " + ReaderSerialNumber);
            Notificar("Lector Conectado", ReaderSerialNumber);
        }

        public void OnReaderDisconnect(object Capture, string ReaderSerialNumber)
        {
            Log("✗ Lector desconectado: " + ReaderSerialNumber);
            Notificar("Lector Desconectado", "Reconecte el lector de huellas");
        }

        public void OnSampleQuality(object Capture, string ReaderSerialNumber, DPFP.Capture.CaptureFeedback feedback)
        {
            if (!_isCapturing || feedback == DPFP.Capture.CaptureFeedback.Good) return;

            string msg = "";
            switch (feedback)
            {
                case DPFP.Capture.CaptureFeedback.TooLight: msg = "Presione más fuerte"; break;
                case DPFP.Capture.CaptureFeedback.TooDark: msg = "Presione más suave"; break;
                case DPFP.Capture.CaptureFeedback.TooNoisy: msg = "Limpie el lector"; break;
                default: msg = "Intente nuevamente"; break;
            }
            Log("⚠ Calidad: " + feedback + " → " + msg);
        }

        // ═══════════════════════════════════════════════════════════════
        //  MÉTODOS AUXILIARES
        // ═══════════════════════════════════════════════════════════════
        private FeatureSet ExtraerCaracteristicas(Sample sample, DataPurpose purpose)
        {
            try
            {
                var extractor = new FeatureExtraction();
                var feedback = DPFP.Capture.CaptureFeedback.None;
                var features = new FeatureSet();

                extractor.CreateFeatureSet(sample, purpose, ref feedback, ref features);
                Log("  Feedback extracción: " + feedback);

                return (feedback == DPFP.Capture.CaptureFeedback.Good) ? features : null;
            }
            catch (Exception ex)
            {
                Log("✗ Error extrayendo features: " + ex.Message);
                return null;
            }
        }

        private Bitmap ConvertirABitmap(Sample sample)
        {
            try
            {
                var conv = new SampleConversion();
                Bitmap bitmap = null;
                conv.ConvertToPicture(sample, ref bitmap);
                return bitmap;
            }
            catch (Exception ex)
            {
                Log("✗ Error convirtiendo bitmap: " + ex.Message);
                return null;
            }
        }

        private string BitmapABase64(Bitmap bitmap)
        {
            using (var ms = new MemoryStream())
            {
                bitmap.Save(ms, ImageFormat.Jpeg); // JPEG: más rápido y liviano que PNG
                return Convert.ToBase64String(ms.ToArray());
            }
        }

        private void Responder(HttpListenerContext ctx, int statusCode, object data)
        {
            try
            {
                ctx.Response.StatusCode = statusCode;
                ctx.Response.ContentType = "application/json; charset=utf-8";

                byte[] buffer = Encoding.UTF8.GetBytes(JsonConvert.SerializeObject(data));
                ctx.Response.ContentLength64 = buffer.Length;
                ctx.Response.OutputStream.Write(buffer, 0, buffer.Length);
                ctx.Response.OutputStream.Close();
            }
            catch { }
        }

        private void Log(string msg)
        {
            try
            {
                string linea = "[" + DateTime.Now.ToString("HH:mm:ss") + "] " + msg;

                if (_logBox.InvokeRequired)
                {
                    _logBox.BeginInvoke(new Action(() => _logBox.AppendText(linea + "\n")));
                }
                else
                {
                    _logBox.AppendText(linea + "\n");
                }

                // Guardar en archivo junto al ejecutable
                try
                {
                    File.AppendAllText(
                        Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "biometric.log"),
                        linea + "\n"
                    );
                }
                catch { }
            }
            catch { }
        }

        private void Notificar(string titulo, string mensaje)
        {
            try
            {
                if (this.InvokeRequired)
                {
                    this.BeginInvoke(new Action(() => Notificar(titulo, mensaje)));
                    return;
                }
                _trayIcon.ShowBalloonTip(3000, titulo, mensaje, ToolTipIcon.Info);
            }
            catch { }
        }

        private void MostrarLogs()
        {
            var f = new Form
            {
                Text = "Logs - Servidor Biométrico",
                Size = new Size(800, 500),
                StartPosition = FormStartPosition.CenterScreen
            };
            var rtb = new RichTextBox
            {
                Dock = DockStyle.Fill,
                Font = new Font("Consolas", 9f),
                BackColor = Color.Black,
                ForeColor = Color.LimeGreen,
                ReadOnly = true,
                Text = _logBox.Text
            };
            f.Controls.Add(rtb);
            f.Show();
        }

        private void CerrarApp()
        {
            if (MessageBox.Show(
                "¿Cerrar el servidor biométrico?\n\nDjango no podrá leer huellas mientras esté cerrado.",
                "Confirmar cierre",
                MessageBoxButtons.YesNo,
                MessageBoxIcon.Warning) == DialogResult.Yes)
            {
                _trayIcon.Visible = false;
                Application.Exit();
            }
        }

        private void OnClosing(object sender, FormClosingEventArgs e)
        {
            try { _httpListener?.Stop(); } catch { }
            try { _capturer?.StopCapture(); } catch { }
            try { _trayIcon.Visible = false; } catch { }
        }
    }
}