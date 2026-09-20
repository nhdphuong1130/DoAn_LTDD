package vn.english7.english7_mobile

import android.media.AudioAttributes
import android.media.MediaPlayer
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel

class MainActivity : FlutterActivity() {
    private val CHANNEL = "vn.english7/audio_player"
    private var mediaPlayer: MediaPlayer? = null
    private var currentUrl: String? = null
    private var isPrepared = false

    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)

        MethodChannel(flutterEngine.dartExecutor.binaryMessenger, CHANNEL).setMethodCallHandler { call, result ->
            when (call.method) {
                "play" -> {
                    val url = call.argument<String>("url")
                    if (url == null) {
                        result.error("INVALID_URL", "Audio URL is null", null)
                        return@setMethodCallHandler
                    }
                    try {
                        if (mediaPlayer != null && currentUrl == url && isPrepared) {
                            if (!mediaPlayer!!.isPlaying) {
                                mediaPlayer!!.start()
                            }
                            result.success(mapOf("status" to "playing", "duration" to mediaPlayer!!.duration))
                            return@setMethodCallHandler
                        }

                        mediaPlayer?.release()
                        isPrepared = false
                        mediaPlayer = MediaPlayer().apply {
                            setAudioAttributes(
                                AudioAttributes.Builder()
                                    .setContentType(AudioAttributes.CONTENT_TYPE_MUSIC)
                                    .setUsage(AudioAttributes.USAGE_MEDIA)
                                    .build()
                            )
                            setDataSource(url)
                            setOnPreparedListener { mp ->
                                isPrepared = true
                                mp.start()
                                result.success(mapOf("status" to "playing", "duration" to mp.duration))
                            }
                            setOnErrorListener { _, what, extra ->
                                result.error("PLAYBACK_ERROR", "MediaPlayer error: $what, extra: $extra", null)
                                true
                            }
                            prepareAsync()
                        }
                        currentUrl = url
                    } catch (e: Exception) {
                        result.error("ERROR", e.message, null)
                    }
                }
                "pause" -> {
                    try {
                        if (mediaPlayer?.isPlaying == true) {
                            mediaPlayer?.pause()
                        }
                        result.success(true)
                    } catch (e: Exception) {
                        result.error("ERROR", e.message, null)
                    }
                }
                "stop" -> {
                    try {
                        mediaPlayer?.stop()
                        mediaPlayer?.release()
                        mediaPlayer = null
                        currentUrl = null
                        isPrepared = false
                        result.success(true)
                    } catch (e: Exception) {
                        result.error("ERROR", e.message, null)
                    }
                }
                "seek" -> {
                    val position = call.argument<Int>("position") ?: 0
                    try {
                        mediaPlayer?.seekTo(position)
                        result.success(true)
                    } catch (e: Exception) {
                        result.error("ERROR", e.message, null)
                    }
                }
                "getStatus" -> {
                    val isPlaying = mediaPlayer?.isPlaying ?: false
                    val position = if (isPrepared) {
                        try { mediaPlayer?.currentPosition ?: 0 } catch (e: Exception) { 0 }
                    } else 0
                    val duration = if (isPrepared) {
                        try { mediaPlayer?.duration ?: 0 } catch (e: Exception) { 0 }
                    } else 0
                    result.success(mapOf("isPlaying" to isPlaying, "position" to position, "duration" to duration))
                }
                else -> result.notImplemented()
            }
        }
    }

    override fun onDestroy() {
        mediaPlayer?.release()
        mediaPlayer = null
        super.onDestroy()
    }
}
