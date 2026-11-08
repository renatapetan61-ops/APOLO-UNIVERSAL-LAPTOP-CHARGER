package com.apolo.charger

import android.Manifest
import android.content.Context
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
import androidx.compose.ui.platform.LocalLifecycleOwner
import androidx.compose.ui.unit.dp
import androidx.compose.ui.viewinterop.AndroidView
import androidx.core.content.ContextCompat
import java.io.File
import java.net.HttpURLConnection
import java.net.URL
import java.util.concurrent.Executors
import kotlin.math.roundToInt

/**
 * AMIS Mobile Camera: uses the phone's own camera to photograph a physically
 * visible motherboard. Images are sent only to the owner's local host agent.
 */
@Composable
fun AmisMobileCameraPanel() {
    val context = LocalContext.current
    val lifecycleOwner = LocalLifecycleOwner.current
    var permissionGranted by remember {
        mutableStateOf(ContextCompat.checkSelfPermission(context, Manifest.permission.CAMERA) == PackageManager.PERMISSION_GRANTED)
    }
    var lensFacing by remember { mutableIntStateOf(CameraSelector.LENS_FACING_BACK) }
    var status by remember { mutableStateOf("Configure a câmera e posicione o celular diante da placa-mãe.") }
    var busy by remember { mutableStateOf(false) }
    var zoom by remember { mutableFloatStateOf(1f) }
    var camera by remember { mutableStateOf<Camera?>(null) }
    var imageCapture by remember { mutableStateOf<ImageCapture?>(null) }
    val executor = remember { Executors.newSingleThreadExecutor() }
    val permissionLauncher = rememberLauncherForActivityResult(ActivityResultContracts.RequestPermission()) { granted ->
        permissionGranted = granted
        status = if (granted) "Permissão concedida. Inicializando câmera." else "Permissão da câmera negada."
    }

    DisposableEffect(Unit) {
        onDispose { executor.shutdown() }
    }

    Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
        Text("AMIS Mobile Camera", style = MaterialTheme.typography.titleMedium)
        Text("Use a câmera do próprio celular para fotografar inscrições que estejam fisicamente visíveis na placa. A câmera do telefone não enxerga através da carcaça.")
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
                    }
                },
                update = { previewView ->
                    val providerFuture = ProcessCameraProvider.getInstance(context)
                    providerFuture.addListener({
                        runCatching {
                            val provider = providerFuture.get()
                            val preview = Preview.Builder().build().also { it.setSurfaceProvider(previewView.surfaceProvider) }
                            val capture = ImageCapture.Builder()
                                .setCaptureMode(ImageCapture.CAPTURE_MODE_MAXIMIZE_QUALITY)
                                .setTargetResolution(Size(1920, 1080))
                                .build()
                            val selector = CameraSelector.Builder().requireLensFacing(lensFacing).build()
                            provider.unbindAll()
                            camera = provider.bindToLifecycle(lifecycleOwner, selector, preview, capture)
                            imageCapture = capture
                            camera?.cameraControl?.setLinearZoom((zoom / 8f).coerceIn(0f, 1f))
                            status = "Câmera pronta. Ajuste o enquadramento e capture a inscrição."
                        }.onFailure { status = "Não foi possível iniciar essa câmera: ${it.message}" }
                    }, ContextCompat.getMainExecutor(context))
                }
            )
            Text("Zoom: ${"%.1f".format(zoom)}×")
            Slider(value = zoom, onValueChange = {
                zoom = it
                camera?.cameraControl?.setLinearZoom(((it - 1f) / 7f).coerceIn(0f, 1f))
            }, valueRange = 1f..8f)
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                Button(enabled = !busy, onClick = {
                    lensFacing = if (lensFacing == CameraSelector.LENS_FACING_BACK) CameraSelector.LENS_FACING_FRONT else CameraSelector.LENS_FACING_BACK
                    status = "Alternando câmera. Aguarde a pré-visualização."
                }) { Text("Alternar câmera") }
                Button(enabled = !busy && imageCapture != null, onClick = {
                    val capture = imageCapture ?: return@Button
                    busy = true
                    status = "Capturando imagem..."
                    val photo = File(context.cacheDir, "amis-board-capture.jpg")
                    val options = ImageCapture.OutputFileOptions.Builder(photo).build()
                    capture.takePicture(options, executor, object : ImageCapture.OnImageSavedCallback {
                        override fun onImageSaved(output: ImageCapture.OutputFileResults) {
                            status = "Imagem capturada. Enviando ao agente local para OCR..."
                            Thread {
                                val result = runCatching {
                                    val bytes = photo.readBytes()
                                    val connection = (URL("http://127.0.0.1:8765/v1/board-inspection").openConnection() as HttpURLConnection)
                                    connection.requestMethod = "POST"
                                    connection.connectTimeout = 5000
                                    connection.readTimeout = 60000
                                    connection.doOutput = true
                                    connection.setRequestProperty("Content-Type", "image/jpeg")
                                    connection.setRequestProperty("Cache-Control", "no-store")
                                    connection.setFixedLengthStreamingMode(bytes.size)
                                    connection.outputStream.use { it.write(bytes) }
                                    val stream = if (connection.responseCode in 200..299) connection.inputStream else connection.errorStream
                                    val body = stream?.bufferedReader()?.use { it.readText() } ?: "Resposta vazia do agente"
                                    val code = connection.responseCode
                                    connection.disconnect()
                                    "HTTP $code\n$body"
                                }.getOrElse { "Falha ao enviar ao agente: ${it.message}. Verifique o agente e a ponte USB/ADB autorizada." }
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
        Text("Privacidade: a imagem é mantida temporariamente no cache do celular, enviada ao agente local em 127.0.0.1 pela ponte autorizada e apagada após o envio. Não há envio para nuvem pelo aplicativo.")
    }
}
