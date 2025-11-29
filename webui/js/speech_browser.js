import { pipeline, read_audio } from './transformers@3.0.2.js';
import { updateChatInput, sendMessage } from '../index.js';

const microphoneButton = document.getElementById('microphone-button');
let microphoneInput = null;
let isProcessingClick = false;

const Status = {
    INACTIVE: 'inactive',
    ACTIVATING: 'activating',
    LISTENING: 'listening',
    RECORDING: 'recording',
    WAITING: 'waiting',
    PROCESSING: 'processing'
};

class MicrophoneInput {
    constructor(updateCallback, options = {}) {
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.lastChunk = [];
        this.updateCallback = updateCallback;
        this.messageSent = false;

        // Audio analysis properties
        this.audioContext = null;
        this.mediaStreamSource = null;
        this.analyserNode = null;
        this._status = Status.INACTIVE;

        // Timing properties
        this.lastAudioTime = null;
        this.waitingTimer = null;
        this.silenceStartTime = null;
        this.hasStartedRecording = false;
        this.analysisFrame = null;

        this.options = {
            modelSize: 'tiny',
            language: 'en',
            silenceThreshold: 0.15,
            silenceDuration: 1000,
            waitingTimeout: 2000,
            minSpeechDuration: 500,
            ...options
        };
    }

    get status() {
        return this._status;
    }

    set status(newStatus) {
        if (this._status === newStatus) return;

        const oldStatus = this._status;
        this._status = newStatus;
        console.log(`Mic status changed from ${oldStatus} to ${newStatus}`);

        // Update UI
        microphoneButton.classList.remove(`mic-${oldStatus.toLowerCase()}`);
        microphoneButton.classList.add(`mic-${newStatus.toLowerCase()}`);
        microphoneButton.setAttribute('data-status', newStatus);

        // Handle state-specific behaviors
        this.handleStatusChange(oldStatus, newStatus);
    }

    handleStatusChange(oldStatus, newStatus) {

        //last chunk kept only for transition to recording status
        if (newStatus != Status.RECORDING) { this.lastChunk = null; }

        switch (newStatus) {
            case Status.INACTIVE:
                this.handleInactiveState();
                break;
            case Status.LISTENING:
                this.handleListeningState();
                break;
            case Status.RECORDING:
                this.handleRecordingState();
                break;
            case Status.WAITING:
                this.handleWaitingState();
                break;
            case Status.PROCESSING:
                this.handleProcessingState();
                break;
        }
    }

    handleInactiveState() {
        this.stopRecording();
        this.stopAudioAnalysis();
        if (this.waitingTimer) {
            clearTimeout(this.waitingTimer);
            this.waitingTimer = null;
        }
    }

    handleListeningState() {
        this.stopRecording();
        this.audioChunks = [];
        this.hasStartedRecording = false;
        this.silenceStartTime = null;
        this.lastAudioTime = null;
        this.messageSent = false;
        this.startAudioAnalysis();
    }

    handleRecordingState() {
        if (!this.hasStartedRecording && this.mediaRecorder.state !== 'recording') {
            this.hasStartedRecording = true;
            this.mediaRecorder.start(1000);
            console.log('Speech started');
        }
        if (this.waitingTimer) {
            clearTimeout(this.waitingTimer);
            this.waitingTimer = null;
        }
    }

    handleWaitingState() {
        // Don't stop recording during waiting state
        this.waitingTimer = setTimeout(() => i18n.t('ui_i18n_t_ui_if_this_status_status_waiting_this_status_status_processing_this_options_waitingtimeout_handleprocessingstate_this_stoprecording_this_process_stoprecording_if_this_mediarecorder_state_recording_this_mediarecorder_stop_this_hasstartedrecording_false_async_initialize_try_this_transcriber_await_pipeline_automatic_speech_recognition_xenova_whisper_this_options_modelsize_this_options_language_const_stream_await_navigator_mediadevices_getusermedia_audio_echocancellation_true_noisesuppression_true_channelcount_1_this_mediarecorder_new_mediarecorder_stream_this_mediarecorder_ondataavailable_event_if_event_data_size_0_this_status_status_recording_this_status_status_waiting_if_this_lastchunk_this_audiochunks_push_this_lastchunk_this_lastchunk_null_this_audiochunks_push_event_data_console_log_audio_chunk_received_total_chunks_this_audiochunks_length_else_if_this_status_status_listening_this_lastchunk_event_data_this_setupaudioanalysis_stream_return_true_catch_error_console_error_microphone_initialization_error_error_window_toastfrontenderror_failed_to_access_microphone_please_check_permissions_microphone_error_return_false_setupaudioanalysis_stream_this_audiocontext_new_window_audiocontext_window_webkitaudiocontext_this_mediastreamsource_this_audiocontext_createmediastreamsource_stream_this_analysernode_this_audiocontext_createanalyser_this_analysernode_fftsize_2048_this_analysernode_mindecibels_90_this_analysernode_maxdecibels_10_this_analysernode_smoothingtimeconstant_0_85_this_mediastreamsource_connect_this_analysernode_startaudioanalysis_const_analyzeframe_if_this_status_status_inactive_return_const_dataarray_new_uint8array_this_analysernode_fftsize_this_analysernode_getbytetimedomaindata_dataarray_calculate_rms_volume_let_sum_0_for_let_i_0_i')< dataArray.length; i++) {
                const amplitude = (dataArray[i] - 128) / 128;
                sum += amplitude * amplitude;
            }
            const rms = Math.sqrt(sum / dataArray.length);

            const now = Date.now();

            // Update status based on audio level
            if (rms > this.options.silenceThreshold) {
                this.lastAudioTime = now;
                this.silenceStartTime = null;

                if (this.status === Status.LISTENING || this.status === Status.WAITING) {
                    if (!speech.isSpeaking()) // TODO? a better way to ignore agent's voice?
                        this.status = Status.RECORDING;
                }
            } else if (this.status === Status.RECORDING) {
                if (!this.silenceStartTime) {
                    this.silenceStartTime = now;
                }

                const silenceDuration = now - this.silenceStartTime;
                if (silenceDuration >= this.options.silenceDuration) {
                    this.status = Status.WAITING;
                }
            }

            this.analysisFrame = requestAnimationFrame(analyzeFrame);
        };

        this.analysisFrame = requestAnimationFrame(analyzeFrame);
    }

    stopAudioAnalysis() {
        if (this.analysisFrame) {
            cancelAnimationFrame(this.analysisFrame);
            this.analysisFrame = null;
        }
    }

    async process() {
        if (this.audioChunks.length === 0) {
            this.status = Status.LISTENING;
            return;
        }

        const audioBlob = new Blob(this.audioChunks, { type: 'audio/wav' });
        const audioUrl = URL.createObjectURL(audioBlob);



        try {
            const samplingRate = 16000;
            const audioData = await read_audio(audioUrl, samplingRate);
            const result = await this.transcriber(audioData);
            const text = this.filterResult(result.text || "")

            if (text) {
                console.log('Transcription:', result.text);
                await this.updateCallback(result.text, true);
            }
        } catch (error) {
            console.error('Transcription error:', error);
            window.toastFrontendError('Transcription failed.', 'Speech Recognition Error');
        } finally {
            URL.revokeObjectURL(audioUrl);
            this.audioChunks = [];
            this.status = Status.LISTENING;
        }
    }

    filterResult(text) {
        text = text.trim()
        let ok = false
        while (!ok) {
            if (!text) break
            if (text[0] === '{' && text[text.length - 1] === '}') break
            if (text[0] === '(' && text[text.length - 1] === ')') break
            if (text[0] === '[' && text[text.length - 1] === ']') break
            ok = true
        }
        if (ok) return text
        else console.log(`Discarding transcription: ${text}`)
    }
}



// Initialize and handle click events
async function initializeMicrophoneInput() {
    microphoneInput = new MicrophoneInput(
        async (text, isFinal) => {
            if (isFinal) {
                updateChatInput(text);
                if (!microphoneInput.messageSent) {
                    microphoneInput.messageSent = true;
                    await sendMessage();
                }
            }
        },
        {
            modelSize: 'tiny',
            language: 'en',
            silenceThreshold: 0.07,
            silenceDuration: 1000,
            waitingTimeout: 1500
        }
    );
    microphoneInput.status = Status.ACTIVATING;

    return await microphoneInput.initialize();
}

microphoneButton.addEventListener('click', async () => {
    if (isProcessingClick) return;
    isProcessingClick = true;

    const hasPermission = await requestMicrophonePermission();
    if (!hasPermission) return;

    try {
        if (!microphoneInput && !await initializeMicrophoneInput()) {
            return;
        }

        // Simply toggle between INACTIVE and LISTENING states
        microphoneInput.status =
            (microphoneInput.status === Status.INACTIVE || microphoneInput.status === Status.ACTIVATING) ? Status.LISTENING : Status.INACTIVE;
    } finally {
        setTimeout(() => {
            isProcessingClick = false;
        }, 300);
    }
});

// Some error handling for microphone input
async function requestMicrophonePermission() {
    try {
        await navigator.mediaDevices.getUserMedia({ audio: true });
        return true;
    } catch (err) {
        console.error('Error accessing microphone:', err);
        window.toastFrontendError('Microphone access denied. Please enable microphone access in your browser settings.', 'Microphone Error');
        return false;
    }
}


class Speech {
    constructor() {
        this.synth = window.speechSynthesis;
        this.utterance = null;
    }

    stripEmojis(str) {
        return str
            .replace(/([\u2700-\u27BF]|[\uE000-\uF8FF]|\uD83C[\uDC00-\uDFFF]|\uD83D[\uDC00-\uDFFF]|[\u2011-\u26FF]|\uD83E[\uDD10-\uDDFF])/g, '')
            .replace(/\s+/g, ' ')
            .trim();
    }

    speak(text) {
        console.log('Speaking:', text);
        // Stop any current utterance
        this.stop();

        // Remove emojis and create a new utterance
        text = this.stripEmojis(text);
        this.utterance = new SpeechSynthesisUtterance(text);

        // Speak the new utterance
        this.synth.speak(this.utterance);
    }

    stop() {
        if (this.isSpeaking()) {
            this.synth.cancel();
        }
    }

    isSpeaking() {
        return this.synth?.speaking || false;
    }
}

export const speech = new Speech();
window.speech = speech
