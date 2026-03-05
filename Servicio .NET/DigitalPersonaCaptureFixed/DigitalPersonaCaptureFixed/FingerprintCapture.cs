using System;
using System.Drawing;
using System.Drawing.Imaging;
using System.IO;
using DPFP;
using DPFP.Capture;
using DPFP.Processing;

namespace DigitalPersonaCaptureFixed
{
    public class FingerprintEventArgs : EventArgs
    {
        public string ImageBase64 { get; set; }
        public string TemplateBase64 { get; set; }
    }

    public class FingerprintCapture : IDisposable
    {
        private Capture _capturer;
        private Enrollment _enroller;
        private int _captureCount = 0;

        public event EventHandler<FingerprintEventArgs> OnFingerprintCaptured;
        public string CurrentPersonaId { get; set; }

        public void Initialize()
        {
            try
            {
                Console.WriteLine("═══════════════════════════════════════════════════════");
                Console.WriteLine("  INICIALIZANDO LECTOR DE HUELLAS");
                Console.WriteLine("═══════════════════════════════════════════════════════");
                Console.WriteLine();

                // Crear instancia del capturer
                _capturer = new Capture();
                _enroller = new Enrollment();

                if (_capturer != null)
                {
                    // Asignar este objeto como manejador de eventos
                    _capturer.EventHandler = new EventHandlerImpl(this);

                    // Iniciar captura
                    _capturer.StartCapture();

                    Console.ForegroundColor = ConsoleColor.Green;
                    Console.WriteLine("✓ Lector de huellas inicializado correctamente");
                    Console.WriteLine("✓ Sistema de captura activado");
                    Console.ResetColor();
                    Console.WriteLine();
                }
                else
                {
                    throw new Exception("No se pudo crear instancia del lector");
                }
            }
            catch (Exception ex)
            {
                Console.ForegroundColor = ConsoleColor.Red;
                Console.WriteLine($"✗ Error inicializando lector: {ex.Message}");
                Console.ResetColor();
                throw;
            }
        }

        public void PrepareForCapture()
        {
            try
            {
                _enroller.Clear();
                _captureCount = 0;
                Console.ForegroundColor = ConsoleColor.Green;
                Console.WriteLine("✓ Lector preparado para nueva captura");
                Console.ResetColor();
            }
            catch (Exception ex)
            {
                Console.WriteLine($"⚠ Advertencia: {ex.Message}");
            }
        }

        public void Dispose()
        {
            try
            {
                if (_capturer != null)
                {
                    _capturer.StopCapture();
                }
            }
            catch { }

            _capturer = null;
            _enroller = null;
        }

        // Clase interna que implementa los eventos
        private class EventHandlerImpl : DPFP.Capture.EventHandler
        {
            private FingerprintCapture _parent;

            public EventHandlerImpl(FingerprintCapture parent)
            {
                _parent = parent;
            }

            public void OnComplete(object Capture, string ReaderSerialNumber, Sample Sample)
            {
                Console.WriteLine();
                Console.ForegroundColor = ConsoleColor.Magenta;
                Console.WriteLine("╔═══════════════════════════════════════════════════════╗");
                Console.WriteLine("║  🔔 HUELLA DETECTADA - PROCESANDO                    ║");
                Console.WriteLine("╚═══════════════════════════════════════════════════════╝");
                Console.ResetColor();
                Console.WriteLine();

                try
                {
                    _parent._captureCount++;
                    Console.ForegroundColor = ConsoleColor.Cyan;
                    Console.WriteLine($"📸 Muestra #{_parent._captureCount} capturada");
                    Console.ResetColor();

                    // Extraer características
                    FeatureSet features = ExtractFeatures(Sample, DataPurpose.Enrollment);

                    if (features != null)
                    {
                        try
                        {
                            // Agregar al enroller
                            _parent._enroller.AddFeatures(features);

                            Console.ForegroundColor = ConsoleColor.Yellow;
                            Console.WriteLine($"📊 Muestras necesarias: {_parent._enroller.FeaturesNeeded}");
                            Console.ResetColor();

                            if (_parent._enroller.FeaturesNeeded > 0)
                            {
                                Console.WriteLine("👆 Levante y vuelva a colocar el dedo");
                                Console.WriteLine();
                            }

                            // Verificar si ya tenemos el template completo
                            if (_parent._enroller.TemplateStatus == Enrollment.Status.Ready)
                            {
                                Console.WriteLine();
                                Console.ForegroundColor = ConsoleColor.Green;
                                Console.WriteLine("╔═══════════════════════════════════════════════════════╗");
                                Console.WriteLine("║  ✓✓✓ TEMPLATE BIOMÉTRICO COMPLETADO ✓✓✓             ║");
                                Console.WriteLine("╚═══════════════════════════════════════════════════════╝");
                                Console.ResetColor();
                                Console.WriteLine();

                                // Convertir a imagen
                                Bitmap bitmap = ConvertSampleToBitmap(Sample);
                                string imageBase64 = null;

                                if (bitmap != null)
                                {
                                    imageBase64 = BitmapToBase64(bitmap);
                                    Console.WriteLine($"✓ Imagen generada: {imageBase64.Length} caracteres");
                                    bitmap.Dispose();
                                }

                                // Obtener template
                                DPFP.Template template = _parent._enroller.Template;
                                byte[] templateBytes = template.Bytes;
                                string templateBase64 = Convert.ToBase64String(templateBytes);
                                Console.WriteLine($"✓ Template generado: {templateBase64.Length} caracteres");
                                Console.WriteLine();

                                // Disparar evento
                                _parent.OnFingerprintCaptured?.Invoke(_parent, new FingerprintEventArgs
                                {
                                    ImageBase64 = imageBase64,
                                    TemplateBase64 = templateBase64
                                });

                                // Limpiar para próxima captura
                                _parent._enroller.Clear();
                                _parent._captureCount = 0;
                            }
                        }
                        catch (Exception ex)
                        {
                            Console.ForegroundColor = ConsoleColor.Red;
                            Console.WriteLine($"✗ Error procesando: {ex.Message}");
                            Console.ResetColor();
                        }
                    }
                    else
                    {
                        Console.ForegroundColor = ConsoleColor.Yellow;
                        Console.WriteLine("⚠ No se extrajeron características válidas");
                        Console.WriteLine("   Intente colocar el dedo nuevamente");
                        Console.ResetColor();
                    }
                }
                catch (Exception ex)
                {
                    Console.ForegroundColor = ConsoleColor.Red;
                    Console.WriteLine($"✗ Error general: {ex.Message}");
                    Console.ResetColor();
                }
            }

            public void OnFingerGone(object Capture, string ReaderSerialNumber)
            {
                Console.ForegroundColor = ConsoleColor.Gray;
                Console.WriteLine("👆 [EVENTO] Dedo retirado");
                Console.ResetColor();
            }

            public void OnFingerTouch(object Capture, string ReaderSerialNumber)
            {
                Console.ForegroundColor = ConsoleColor.Cyan;
                Console.WriteLine();
                Console.WriteLine("👇 [EVENTO] ¡DEDO DETECTADO! Capturando...");
                Console.ResetColor();
            }

            public void OnReaderConnect(object Capture, string ReaderSerialNumber)
            {
                Console.ForegroundColor = ConsoleColor.Green;
                Console.WriteLine($"✓ [EVENTO] Lector conectado: {ReaderSerialNumber}");
                Console.ResetColor();
            }

            public void OnReaderDisconnect(object Capture, string ReaderSerialNumber)
            {
                Console.ForegroundColor = ConsoleColor.Red;
                Console.WriteLine($"✗ [EVENTO] Lector desconectado: {ReaderSerialNumber}");
                Console.ResetColor();
            }

            public void OnSampleQuality(object Capture, string ReaderSerialNumber, CaptureFeedback CaptureFeedback)
            {
                if (CaptureFeedback == CaptureFeedback.Good)
                {
                    Console.ForegroundColor = ConsoleColor.Green;
                    Console.WriteLine("✓ [EVENTO] Calidad: EXCELENTE");
                    Console.ResetColor();
                }
                else
                {
                    Console.ForegroundColor = ConsoleColor.Yellow;
                    Console.WriteLine($"⚠ [EVENTO] Calidad: {CaptureFeedback}");

                    switch (CaptureFeedback)
                    {
                        case CaptureFeedback.TooLight:
                            Console.WriteLine("   → Presione MÁS FUERTE");
                            break;
                        case CaptureFeedback.TooDark:
                            Console.WriteLine("   → Presione MÁS SUAVE");
                            break;
                        case CaptureFeedback.TooNoisy:
                            Console.WriteLine("   → LIMPIE el lector y su dedo");
                            break;
                        default:
                            Console.WriteLine("   → Intente de nuevo");
                            break;
                    }
                    Console.ResetColor();
                }
            }

            private FeatureSet ExtractFeatures(Sample sample, DataPurpose purpose)
            {
                try
                {
                    FeatureExtraction extractor = new FeatureExtraction();
                    CaptureFeedback feedback = CaptureFeedback.None;
                    FeatureSet features = new FeatureSet();

                    extractor.CreateFeatureSet(sample, purpose, ref feedback, ref features);

                    if (feedback == CaptureFeedback.Good)
                    {
                        return features;
                    }

                    return null;
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"Error extrayendo características: {ex.Message}");
                    return null;
                }
            }

            private Bitmap ConvertSampleToBitmap(Sample sample)
            {
                try
                {
                    SampleConversion converter = new SampleConversion();
                    Bitmap bitmap = null;
                    converter.ConvertToPicture(sample, ref bitmap);
                    return bitmap;
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"Error convirtiendo imagen: {ex.Message}");
                    return null;
                }
            }

            private string BitmapToBase64(Bitmap bitmap)
            {
                try
                {
                    using (MemoryStream ms = new MemoryStream())
                    {
                        bitmap.Save(ms, ImageFormat.Png);
                        byte[] bytes = ms.ToArray();
                        return Convert.ToBase64String(bytes);
                    }
                }
                catch (Exception ex)
                {
                    Console.WriteLine($"Error convirtiendo a Base64: {ex.Message}");
                    return null;
                }
            }
        }
    }
}