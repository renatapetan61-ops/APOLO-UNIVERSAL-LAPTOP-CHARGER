package com.apolo.charger

import android.Manifest
import android.content.pm.PackageManager
import android.util.Size
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.camera.core.Camera
import androidx.camera.core.CameraSelector
import androidx.camera.core.ImageCapture
import androidx.camera.core.ImageCaptureException
import androidx.camera.core.Preview
import androidx.camera.lifecycle.ProcessCameraProvider
import androidx.camera.view.PreviewView
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Slider
import androidx.compose.material3.Text
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.lifecycle.compose.LocalLifecycleOwner
import androidx.compose.ui.unit.dp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.core.content.ContextCompat
import java.io.File
import java.net.HttpURLConnection
import java.net.URL
import java.util.concurrent.Executors

/** Uses the phone camera to photograph a motherboard that is physically visible. */
@Composable
fun AmisMobileCameraPanel() {
    val context = LocalContext.current
    val lifecycleOwner = LocalLifecycleOwner.current
    var permissionGranted by remember {
        mutableStateOf(ContextCompat.checkSelfPermission(context, Manifest.permission.CAMERA) == PackageManager.PERMISSION_GRANTED)
    }
    var lensFacing by remember { mutableIntStateOf(CameraSelector.LENS_FACING_BACK) }
    var status by remember { mutableStateOf("Permita o acesso à câmera para iniciar a inspeção.") }
    var busy by remember { mutableStateOf(false) }
    var zoom by remember { mutableFloatStateOf(1f) }
    var camera by remember { mutableStateOf<Camera?>(null) }
    var imageCapture by remember { mutableStateOf<ImageCapture?>(null) }
    var previewView by remember { mutableStateOf<PreviewView?>(null) }
    val captureExecutor = remember { Executors.newSingleThreadExecutor() }
    val permissionLauncher = rememberLauncherForActivityResult(ActivityResultContracts.RequestPermission()) { granted ->
        permissionGranted = granted
        status = if (granted) "Permissão concedida. Preparando câmera." else "Permissão da câmera negada."
    }

    DisposableEffect(Unit) {
        onDispose { captureExecutor.shutdown() }
    }

    LaunchedEffect(previewView, permissionGranted, lensFacing, lifecycleOwner) {
        val view = previewView
        if (view != null && permissionGranted) {
            val providerFuture = ProcessCameraProvider.getInstance(context)
            providerFuture.addListener({
                runCatching {
                    val provider = providerFuture.get()
                    val preview = Preview.Builder().build().also { it.setSurfaceProvider(view.surfaceProvider) }
                    val capture = ImageCapture.Builder()
                        .setCaptureMode(ImageCapture.CAPTURE_MODE_MAXIMIZE_QUALITY)
                        .setTargetResolution(Size(1920, 1080))
                        .build()
                    val selector = CameraSelector.Builder().requireLensFacing(lensFacing).build()
                    provider.unbindAll()
                    camera = provider.bindToLifecycle(lifecycleOwner, selector, preview, capture)
                    imageCapture = capture
                    camera?.cameraControl?.setLinearZoom(((zoom - 1f) / 7f).coerceIn(0f, 1f))
                    status = "Câmera pronta. Enquadre a inscrição da placa-mãe."
                }.onFailure {
                    status = "Não foi possível iniciar essa câmera: ${it.message}"
                    imageCapture = null
                }
            }, ContextCompat.getMainExecutor(context))
        }
    }

    DisposableEffect(lifecycleOwner) {
        onDispose {
            runCatching { ProcessCameraProvider.getInstance(context).get().unbindAll() }
            camera = null
            imageCapture = null
        }
    }

    Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
        Text("AMIS Mobile Camera", style = MaterialTheme.typography.titleMedium)
        Text("Configure e use a câmera do próprio celular. Para fotografar a placa, ela precisa estar fisicamente visível; a câmera não enxerga através da carcaça.")
        if (!permissionGranted) {
            Button(onClick = { permissionLauncher.launch(Manifest.permission.CAMERA) }) {
                Text("Permitir acesso à câmera")
            }
        } else {
            AndroidView(
                modifier = Modifier.fillMaxWidth().height(260.dp),
                factory = { ctx ->
                    PreviewView(ctx).apply {
                        scaleType = PreviewView.ScaleType.FILL_CENTER
                        implementationMode = PreviewView.ImplementationMode.COMPATIBLE
                        previewView = this
                    }
                }
            )
            Text("Zoom digital: ${"%.1f".format(zoom)}×")
            Slider(value = zoom, onValueChange = {
                zoom = it
                camera?.cameraControl?.setLinearZoom(((it - 1f) / 7f).coerceIn(0f, 1f))
            }, valueRange = 1f..8f)
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                Button(enabled = !busy, onClick = {
                    lensFacing = if (lensFacing == CameraSelector.LENS_FACING_BACK) CameraSelector.LENS_FACING_FRONT else CameraSelector.LENS_FACING_BACK
                    status = "Alternando câmera..."
                }) { Text("Alternar câmera") }
                Button(enabled = !busy && imageCapture != null, onClick = {
                    val capture = imageCapture ?: return@Button
                    busy = true
                    status = "Capturando imagem..."
                    val photo = File(context.cacheDir, "amis-board-capture.jpg")
                    val options = ImageCapture.OutputFileOptions.Builder(photo).build()
                    capture.takePicture(options, captureExecutor, object : ImageCapture.OnImageSavedCallback {
                        override fun onImageSaved(output: ImageCapture.OutputFileResults) {
                            status = "Foto capturada. Enviando ao agente local para OCR..."
                            Thread {
                                val result = runCatching {
                                    val bytes = photo.readBytes()
                                    require(bytes.size <= 8 * 1024 * 1024) { "Imagem maior que o limite de 8 MiB" }
                                    val connection = URL("http://127.0.0.1:8765/v1/board-inspection").openConnection() as HttpURLConnection
                                    connection.requestMethod = "POST"
                                    connection.connectTimeout = 5000
                                    connection.readTimeout = 60000
                                    connection.doOutput = true
                                    connection.setRequestProperty("Content-Type", "image/jpeg")
                                    connection.setRequestProperty("Cache-Control", "no-store")
                                    connection.setFixedLengthStreamingMode(bytes.size)
                                    connection.outputStream.use { it.write(bytes) }
                                    val code = connection.responseCode
                                    val stream = if (code in 200..299) connection.inputStream else connection.errorStream
                                    val body = stream?.bufferedReader()?.use { it.readText() } ?: "Resposta vazia do agente"
                                    connection.disconnect()
                                    "HTTP $code\n$body"
                                }.getOrElse {
                                    "Falha ao enviar ao agente: ${it.message}. Verifique o agente e a ponte USB/ADB autorizada."
                                }
                                photo.delete()
                                android.os.Handler(android.os.Looper.getMainLooper()).post {
                                    status = result
                                    busy = false
                                }
                            }.start()
                        }
                        override fun onError(exception: ImageCaptureException) {
                            status = "Falha na captura: ${exception.message}"
                            busy = false
                            photo.delete()
                        }
                    })
                }) { Text(if (busy) "Processando..." else "Fotografar e analisar placa") }
            }
        }
        Text(status, style = MaterialTheme.typography.bodySmall)
        Text("A foto é processada localmente: fica temporariamente no cache, é enviada ao agente em 127.0.0.1 pela ponte autorizada e apagada após o envio. O aplicativo não envia a imagem para a nuvem.")
    }
}
