using System;
using System.IO;
using System.Net;
using System.Threading;
using Newtonsoft.Json;

namespace DigitalPersonaCaptureFixed
{
    public class AutomaticFingerprintService
    {
        private readonly string _djangoUrl;
        private readonly string _signalPath;
        private FingerprintCapture _capture;
        private Thread _monitorThread;
        private bool _isRunning;
        private string _lastProcessedId;
        private bool _isCapturing;
        private readonly object _lock = new object();

        public AutomaticFingerprintService(string djangoUrl, string signalPath)
        {
            _djangoUrl = djangoUrl;
            _signalPath = signalPath;
            _capture = new FingerprintCapture();
            _lastProcessedId = "";
            _isCapturing = false;
        }

        public void Start()
        {
            _isRunning = true;

            // Inicializar lector
            Console.WriteLine("🔌 Inicializando lector de huellas...");
            _capture.Initialize();
            _capture.OnFingerprintCaptured += OnFingerprintCaptured;

            // Iniciar hilo de monitoreo
            _monitorThread = new Thread(MonitorSignals)
            {
                IsBackground = true,
                Name = "SignalMonitorThread"
            };
            _monitorThread.Start();

            Console.ForegroundColor = ConsoleColor.Green;
            Console.WriteLine("✓ Monitor de señales iniciado");
            Console.ResetColor();
        }

        public void Stop()
        {
            _isRunning = false;

            if (_capture != null)
            {
                _capture.Dispose();
            }

            if (_monitorThread != null && _monitorThread.IsAlive)
            {
                _monitorThread.Join(2000);
            }
        }

        private void MonitorSignals()
        {
            string signalFile = Path.Combine(_signalPath, "current_person.txt");

            Console.ForegroundColor = ConsoleColor.Cyan;
            Console.WriteLine($"👁  Monitoreando: {signalFile}");
            Console.ResetColor();

            // Limpiar cualquier señal anterior
            try
            {
                if (File.Exists(signalFile))
                {
                    File.Delete(signalFile);
                    Console.WriteLine("🧹 Señales anteriores limpiadas");
                }
            }
            catch { }

            while (_isRunning)
            {
                try
                {
                    if (File.Exists(signalFile))
                    {
                        string personaId = File.ReadAllText(signalFile).Trim();

                        lock (_lock)
                        {
                            // CAMBIO CRÍTICO: Permitir el mismo ID si no está capturando
                            if (!string.IsNullOrEmpty(personaId) && !_isCapturing)
                            {
                                // Solo actualizar si es diferente O si no hay captura en proceso
                                if (personaId != _lastProcessedId)
                                {
                                    _lastProcessedId = personaId;
                                    _isCapturing = true;

                                    Console.WriteLine();
                                    Console.ForegroundColor = ConsoleColor.Yellow;
                                    Console.WriteLine("═══════════════════════════════════════════════════════");
                                    Console.WriteLine($"  🆕 NUEVA PERSONA DETECTADA - ID: {personaId}");
                                    Console.WriteLine("═══════════════════════════════════════════════════════");
                                    Console.ResetColor();
                                    Console.WriteLine();

                                    _capture.CurrentPersonaId = personaId;

                                    // CRÍTICO: Reiniciar el lector para esta captura
                                    Console.WriteLine("🔄 Preparando lector para captura...");
                                    _capture.PrepareForCapture();

                                    Console.ForegroundColor = ConsoleColor.Cyan;
                                    Console.WriteLine("🖐  Por favor, coloque su dedo en el lector...");
                                    Console.WriteLine("    (Presione firmemente durante 2 segundos)");
                                    Console.ResetColor();
                                    Console.WriteLine();
                                }
                            }
                        }
                    }
                }
                catch (IOException)
                {
                    // Archivo siendo usado, reintentar
                }
                catch (Exception ex)
                {
                    if (!(ex is FileNotFoundException))
                    {
                        Console.ForegroundColor = ConsoleColor.Yellow;
                        Console.WriteLine($"⚠ Advertencia en monitor: {ex.Message}");
                        Console.ResetColor();
                    }
                }

                Thread.Sleep(500); // Verificar cada medio segundo (más rápido)
            }
        }

        private void OnFingerprintCaptured(object sender, FingerprintEventArgs e)
        {
            lock (_lock)
            {
                Console.WriteLine();
                Console.ForegroundColor = ConsoleColor.Green;
                Console.WriteLine("═══════════════════════════════════════════════════════");
                Console.WriteLine("  ✓ HUELLA CAPTURADA EXITOSAMENTE");
                Console.WriteLine("═══════════════════════════════════════════════════════");
                Console.ResetColor();
                Console.WriteLine();

                string personaId = _capture.CurrentPersonaId;

                if (string.IsNullOrEmpty(personaId))
                {
                    Console.ForegroundColor = ConsoleColor.Red;
                    Console.WriteLine("✗ Error: No hay ID de persona configurado");
                    Console.ResetColor();
                    _isCapturing = false;
                    return;
                }

                Console.WriteLine($"📋 Persona ID: {personaId}");
                Console.WriteLine($"📸 Imagen capturada: {(e.ImageBase64 != null ? e.ImageBase64.Length : 0)} caracteres");
                Console.WriteLine($"🔐 Template creado: {(e.TemplateBase64 != null ? e.TemplateBase64.Length : 0)} caracteres");
                Console.WriteLine();
                Console.ForegroundColor = ConsoleColor.Cyan;
                Console.WriteLine("📤 Enviando datos a Django...");
                Console.ResetColor();

                bool enviado = SendToDjango(personaId, e.ImageBase64, e.TemplateBase64);

                if (enviado)
                {
                    Console.WriteLine();
                    Console.ForegroundColor = ConsoleColor.Green;
                    Console.WriteLine("═══════════════════════════════════════════════════════");
                    Console.WriteLine("  ✅ REGISTRO COMPLETADO EXITOSAMENTE");
                    Console.WriteLine("═══════════════════════════════════════════════════════");
                    Console.ResetColor();
                    Console.WriteLine();
                    Console.ForegroundColor = ConsoleColor.White;
                    Console.WriteLine("⏳ Listo para siguiente registro...");
                    Console.ResetColor();
                    Console.WriteLine();

                    // Limpiar archivo de señal
                    try
                    {
                        string signalFile = Path.Combine(_signalPath, "current_person.txt");
                        if (File.Exists(signalFile))
                        {
                            File.Delete(signalFile);
                        }
                    }
                    catch (Exception ex)
                    {
                        Console.WriteLine($"⚠ No se pudo eliminar señal: {ex.Message}");
                    }
                }
                else
                {
                    Console.WriteLine();
                    Console.ForegroundColor = ConsoleColor.Red;
                    Console.WriteLine("✗ ERROR: No se pudo enviar la huella a Django");
                    Console.WriteLine("   Verifique que Django esté corriendo en: " + _djangoUrl);
                    Console.ResetColor();
                    Console.WriteLine();
                }

                _isCapturing = false;
            }
        }

        private bool SendToDjango(string personaId, string imageBase64, string templateBase64)
        {
            try
            {
                var data = new
                {
                    persona_id = personaId,
                    huella_imagen = imageBase64,
                    huella_template = templateBase64
                };

                string json = JsonConvert.SerializeObject(data);

                using (var client = new WebClient())
                {
                    client.Headers[HttpRequestHeader.ContentType] = "application/json";
                    client.Encoding = System.Text.Encoding.UTF8;

                    string response = client.UploadString(_djangoUrl, "POST", json);

                    // Verificar respuesta
                    var result = JsonConvert.DeserializeObject<dynamic>(response);

                    if (result.success == true)
                    {
                        Console.ForegroundColor = ConsoleColor.Green;
                        Console.WriteLine("✓ Django confirmó la recepción correctamente");
                        Console.ResetColor();
                        return true;
                    }
                    else
                    {
                        Console.ForegroundColor = ConsoleColor.Yellow;
                        Console.WriteLine($"⚠ Django respondió: {response}");
                        Console.ResetColor();
                        return false;
                    }
                }
            }
            catch (WebException ex)
            {
                Console.ForegroundColor = ConsoleColor.Red;
                Console.WriteLine($"✗ Error de conexión: {ex.Message}");

                if (ex.Response != null)
                {
                    using (var reader = new StreamReader(ex.Response.GetResponseStream()))
                    {
                        string errorResponse = reader.ReadToEnd();
                        Console.WriteLine($"   Respuesta del servidor: {errorResponse}");
                    }
                }
                Console.ResetColor();
                return false;
            }
            catch (Exception ex)
            {
                Console.ForegroundColor = ConsoleColor.Red;
                Console.WriteLine($"✗ Error enviando datos: {ex.Message}");
                Console.ResetColor();
                return false;
            }
        }
    }
}