package vn.english7.english7_mobile

import android.Manifest
import android.app.Activity
import android.content.pm.PackageManager
import android.media.AudioFormat
import android.media.AudioRecord
import android.media.MediaPlayer
import android.media.MediaRecorder
import android.os.Build
import io.flutter.plugin.common.BinaryMessenger
import io.flutter.plugin.common.MethodChannel
import java.io.ByteArrayOutputStream
import java.io.File
import java.nio.ByteBuffer
import java.nio.ByteOrder

/** Bounded mono PCM capture. Raw recordings live only in memory. */
class SpeechRecorderChannel(private val activity: Activity, messenger: BinaryMessenger) {
    private val channel = MethodChannel(messenger, "english7/speech")
    private var pendingPermission: MethodChannel.Result? = null
    private var recorder: AudioRecord? = null
    private var worker: Thread? = null
    @Volatile private var recording = false
    @Volatile private var pcm: ByteArray? = null
    private var player: MediaPlayer? = null
    private var playbackFile: File? = null
    private var generation = 0
    companion object { const val PERMISSION_REQUEST = 7307; const val SAMPLE_RATE = 16000 }

    init {
        channel.setMethodCallHandler { call, result ->
            try {
                when (call.method) {
                    "start" -> {
                        if (pendingPermission != null || recording) {
                            result.error("busy", "A recording is already active", null)
                        } else if (Build.VERSION.SDK_INT >= 23 && activity.checkSelfPermission(Manifest.permission.RECORD_AUDIO) != PackageManager.PERMISSION_GRANTED) {
                            pendingPermission = result
                            activity.requestPermissions(arrayOf(Manifest.permission.RECORD_AUDIO), PERMISSION_REQUEST)
                        } else start(result)
                    }
                    "stop" -> {
                        stopCapture()
                        val bytes = pcm
                        pcm = null
                        if (bytes == null || bytes.isEmpty()) result.error("empty_recording", "Record again", null)
                        else result.success(wav(bytes))
                    }
                    "play" -> play(call.arguments as ByteArray, result)
                    "dispose" -> { dispose(); result.success(null) }
                    else -> result.notImplemented()
                }
            } catch (e: Exception) {
                dispose()
                result.error("audio_error", e.message, null)
            }
        }
    }

    fun permissionResult(requestCode: Int, grantResults: IntArray): Boolean {
        if (requestCode != PERMISSION_REQUEST) return false
        val result = pendingPermission ?: return true
        pendingPermission = null
        if (grantResults.firstOrNull() == PackageManager.PERMISSION_GRANTED) {
            try { start(result) } catch (e: Exception) { dispose(); result.error("audio_error", e.message, null) }
        } else result.error("permission_denied", "Microphone permission was denied", null)
        return true
    }

    @Suppress("MissingPermission")
    private fun start(result: MethodChannel.Result) {
        stopCapture()
        stopPlayback()
        pcm = null
        val minimum = AudioRecord.getMinBufferSize(SAMPLE_RATE, AudioFormat.CHANNEL_IN_MONO, AudioFormat.ENCODING_PCM_16BIT)
        check(minimum > 0) { "Microphone does not support PCM capture" }
        val capture = AudioRecord(MediaRecorder.AudioSource.MIC, SAMPLE_RATE, AudioFormat.CHANNEL_IN_MONO, AudioFormat.ENCODING_PCM_16BIT, maxOf(minimum, 6400))
        recorder = capture
        check(capture.state == AudioRecord.STATE_INITIALIZED) { "Microphone is unavailable" }
        capture.startRecording()
        recording = true
        worker = Thread {
            val output = ByteArrayOutputStream()
            val buffer = ByteArray(3200)
            val limit = SAMPLE_RATE * 2 * 15
            try {
                while (recording && output.size() < limit) {
                    val count = capture.read(buffer, 0, minOf(buffer.size, limit - output.size()))
                    if (count <= 0) break
                    output.write(buffer, 0, count)
                }
                pcm = output.toByteArray()
            } finally {
                recording = false
                try { capture.stop() } catch (_: Exception) { }
            }
        }.apply { name = "english7-speech-capture"; start() }
        result.success(null)
    }

    fun stopCapture() {
        recording = false
        try { recorder?.stop() } catch (_: Exception) { }
        worker?.join(1000)
        worker = null
        recorder?.release()
        recorder = null
    }

    private fun wav(bytes: ByteArray): ByteArray {
        val header = ByteBuffer.allocate(44).order(ByteOrder.LITTLE_ENDIAN)
        header.put("RIFF".toByteArray()).putInt(36 + bytes.size).put("WAVEfmt ".toByteArray())
        header.putInt(16).putShort(1.toShort()).putShort(1.toShort()).putInt(SAMPLE_RATE)
        header.putInt(SAMPLE_RATE * 2).putShort(2.toShort()).putShort(16.toShort())
        header.put("data".toByteArray()).putInt(bytes.size)
        return header.array() + bytes
    }

    private fun play(bytes: ByteArray, result: MethodChannel.Result) {
        require(bytes.size <= 12 * 1024 * 1024) { "Audio exceeds playback limit" }
        stopPlayback()
        val token = generation
        val file = File.createTempFile("english7-speech-", ".audio", activity.cacheDir)
        playbackFile = file
        file.writeBytes(bytes)
        var replied = false
        player = MediaPlayer().apply {
            setDataSource(file.absolutePath)
            setOnPreparedListener {
                if (generation == token) {
                    it.start()
                    if (!replied) { replied = true; result.success(null) }
                }
            }
            setOnCompletionListener { if (generation == token) stopPlayback() }
            setOnErrorListener { _, _, _ ->
                if (!replied) { replied = true; result.error("playback_error", "Cannot play audio", null) }
                if (generation == token) stopPlayback()
                true
            }
            prepareAsync()
        }
    }

    private fun stopPlayback() {
        generation++
        player?.release()
        player = null
        playbackFile?.delete()
        playbackFile = null
    }

    fun dispose() {
        pendingPermission?.error("cancelled", "Recording was cancelled", null)
        pendingPermission = null
        stopCapture()
        pcm = null
        stopPlayback()
    }
}
