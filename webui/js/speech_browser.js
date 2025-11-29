import { pipeline, read_audio } from 'i18n.t('ui_transformers_3_0_2_js')';
import { updateChatInput, sendMessage } from 'i18n.t('ui_index_js')';

const microphoneButton = document.getElementById('i18n.t('ui_microphone_button')');
let microphoneInput = null;
let isProcessingClick = false;

const Status = {
    INACTIVE: 'i18n.t('ui_inactive')',
    ACTIVATING: 'i18n.t('ui_activating')',
    LISTENING: 'i18n.t('ui_listening')',
    RECORDING: 'i18n.t('ui_recording')',
    WAITING: 'i18n.t('ui_waiting')',
    PROCESSING: 'i18n.t('ui_processing')'
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

        i18n.t('ui_mic_status_changed_from_oldstatus_to_newstatus')ll;
        this.waitingTimer = null;
        this.silenceStartTime =i18n.t('ui_mic_oldstatus_tolowercase')Recording = false;
        this.analysisFrami18n.t('ui_mic_newstatus_tolowercase')s = {
            modelSize: 'i18n.t('ui_tiny')',
            language: 'i18n.t('ui_en')',
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
        microphoneButton.setAttribute('i18n.t('ui_data_status')', newStatus);

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
       i18n.t('ui_i18n_t_ui_i18n_t_ui_if_this_status_status_waiting_this_status_status_processing_this_options_waitingtimeout_handleprocessingstate_this_stoprecording_this_process_stoprecording_if_this_mediarecorder_state_recording_this_mediarecorder_stop_this_hasstartedrecording_false_async_initialize_try_this_transcriber_await_pipeline_automatic_speech_recognition_xenova_whisper_this_options_modelsize_this_options_language_const_stream_await_navigator_mediadevices_getusermedia_audio_echocancellation_true_noisesuppression_true_channelcount_1_this_mediarecorder_new_mediarecorder_stream_this_mediarecorder_ondataavailable_event_if_event_data_size_0_this_status_status_recording_this_status_status_waiting_if_this_lastchunk_this_audiochunks_push_this_lastchunk_this_lastchunk_null_this_audiochunks_push_event_data_console_log_audio_chunk_received_total_chunks_this_audiochunks_length_else_if_this_status_status_listening_this_lastchunk_event_data_this_setupaudioanalysis_stream_return_true_catch_error_console_error_microphone_initialization_error_error_window_toastfrontenderror_failed_to_access_microphone_please_check_permissions_microphone_error_return_false_setupaudioanalysis_stream_this_audiocontext_new_window_audiocontext_window_webkitaudiocontext_this_mediastreamsource_this_audiocontext_createmediastreamsource_stream_this_analysernode_this_audiocontext_createanalyser_this_analysernode_fftsize_2048_this_analysernode_mindecibels_90_this_analysernode_maxdecibels_10_this_analysernode_smoothingtimeconstant_0_85_this_mediastreamsource_connect_this_analysernode_startaudioanalysis_const_analyzeframe_if_this_status_status_inactive_return_const_dataarray_new_uint8array_this_analysernode_fftsize_this_analysernode_getbytetimedomaindata_dataarray_calculate_rms_volume_let_sum_0_for_let_i_0_i')rror_window_toastfrontenderror_failed_to_access_microphone_please_check_permissions_microphone_error_return_false_setupaudioanalysis_stream_this_audiocontext_new_window_audiocontext_window_webkitaudiocontext_this_mediastreamsource_this_audiocontext_createmediastreamsource_stream_this_analysernode_this_audiocontext_createanalyser_this_analysernode_fftsize_2048_this_analysernode_mindecibels_90_this_analysernode_maxdecibels_10_this_analysernode_smoothingtimeconstant_0_85_this_mediastreamsource_connect_this_analysernode_startaudioanalysis_const_analyzeframe_if_this_status_status_inactive_return_const_dataarray_new_uint8array_this_analysernode_fftsize_this_analysernode_getbytetimedomaindata_dataarray_calculate_rms_volume_let_sum_0_for_let_i_0_i'i18n.t('ui_dataarray_length_i_const_amplitude_dataarray_i_128_128_sum_amplitude_amplitude_const_rms_math_sqrt_sum_dataarray_length_const_now_date_now_update_status_based_on_audio_level_if_rms_this_options_silencethreshold_this_lastaudiotime_now_this_silencestarttime_null_if_this_status_status_listening_this_status_status_waiting_if_speech_isspeaking_todo_a_better_way_to_ignore_agent')'s voice?
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

        const audioBlob = new Blob(this.audioChunks, { type: 'i18n.t('ui_audio_wav')' });
        const audioUrl = URL.createObjectURL(audioBlob);



        try {
            const samplingRate = 16000;
            const audioData = await read_audio(audioUrl, samplingRate);
            const result = await this.transcriber(audioData);
            const text = this.filterResult(result.text || "")

            if (text) {
                console.log('i18n.t('ui_transcription')', result.text);
                await this.updateCallback(result.text, true);
            }
        } catch (error) {
            console.error('i18n.t('ui_transcription_error')', error);
            window.toastFrontendError('i18n.t('ui_transcription_failed')', 'i18n.t('ui_speech_recognition_erri18n.t('ui_discarding_transcription_text')       URL.revokeObjectURL(audioUrl);
            this.audioChunks = [];
            this.status = Status.LISTENING;
        }
    }

    filterResult(text) {
        text = text.trim()
        let ok = false
        while (!ok) {
            if (!text) break
            if (text[0] === '{'i18n.t('ui_text_text_length_1')'}'i18n.t('ui_break_if_text_0')'('i18n.t('ui_text_text_length_1')')'i18n.t('ui_break_if_text_0')'['i18n.t('ui_text_text_length_1')']'i18n.t('ui_break_ok_true_if_ok_return_text_else_console_log_discarding_transcription_text_initialize_and_handle_click_events_async_function_initializemicrophoneinput_microphoneinput_new_microphoneinput_async_text_isfinal_if_isfinal_updatechatinput_text_if_microphoneinput_messagesent_microphoneinput_messagesent_true_await_sendmessage_modelsize')'tiny'i18n.t('ui_language')'en'i18n.t('ui_silencethreshold_0_07_silenceduration_1000_waitingtimeout_1500_microphoneinput_status_status_activating_return_await_microphoneinput_initialize_microphonebutton_addeventlistener')'click'i18n.t('ui_async_if_isprocessingclick_return_isprocessingclick_true_const_haspermission_await_requestmicrophonepermission_if_haspermission_return_try_if_microphoneinput_await_initializemicrophoneinput_return_simply_toggle_between_inactive_and_listening_states_microphoneinput_status_microphoneinput_status_status_inactive_microphoneinput_status_status_activating_status_listening_status_inactive_finally_settimeout_isprocessingclick_false_300_some_error_handling_for_microphone_input_async_function_requestmicrophonepermission_try_await_navigator_mediadevices_getusermedia_audio_true_return_true_catch_err_console_error')'Error accessing microphone:'i18n.t('ui_err_window_toastfrontenderror')'Microphone access denied. Please enable microphone access in your browser settings.'i18n.t('ui_')'Microphone Error');
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
            .replace(/\s+/g, ' 'i18n.t('ui_trim_speak_text_console_log')'Speaking:', text);
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
