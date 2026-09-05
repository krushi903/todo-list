import numpy as np 
import matplotlib.pyplot as plt 
import matplotlib.animation as animation
from matplotlib.widgets import Button 
import sounddevice as sd
import librosa
import noisereduce as nr
from scipy.signal import butter, filtfilt
import threading 
import queue 

plt.switch_backend('TkAgg')

# =============================
# CONFIG
# =============================
duration = 10
sr = 44100 
CHUNK = 1024 

# =============================
# GLOBAL STATE
# =============================
audio           = None 
enhanced_audio  = None 
filtered_signals = {} 
is_recording    = False
audio_queue     = queue.Queue() 
live_buffer     = np.zeros(sr * 3, dtype=np.float32) 

# =============================
# FILTER FUNCTIONS  (same as original)
# =============================
def highpass(signal, cutoff=120, order=5):
    nyq = 0.5 * sr
    b, a = butter(order, cutoff / nyq, btype='high')
    return filtfilt(b, a, signal)

def highpass_strong(signal, cutoff=180, order=5):
    nyq = 0.5 * sr
    b, a = butter(order, cutoff / nyq, btype='high')
    return filtfilt(b, a, signal)  

def bandpass(data, lowcut=190, highcut=4000, order=5):
    nyq = 0.5 * sr
    low  = max(lowcut  / nyq, 1e-4)
    high = min(highcut / nyq, 0.9999)
    b, a = butter(order, [low, high], btype='band')
    return filtfilt(b, a, data)

bands = {
    "Red (Bass)":         (20,   120),
    "Green (Speech Clean)":(120,  1000),
    "Blue (Clarity)":     (1000, 4000),
    "Purple (High)":      (4000, sr // 2 - 100),
}

# =============================
# PROCESSING  (same as original)
# =============================
def process_and_update(raw):
    global audio, enhanced_audio, filtered_signals 

    audio = raw.flatten().astype(np.float64)
    audio = audio / (np.max(np.abs(audio)) + 1e-6)

    # Step 1: Noise reduction
    noise_sample  = audio[:int(sr * 1.5)]
    reduced_noise = nr.reduce_noise(
        y=audio, sr=sr, y_noise=noise_sample,
        prop_decrease=0.9, stationary=False,
        n_fft=1024, hop_length=256
    )

    # Step 2: High pass
    clean_stage1 = highpass(reduced_noise, cutoff=120)

    # Step 3: HPSS enhancement
    S = librosa.stft(clean_stage1, n_fft=1024, hop_length=256)
    harmonic, percussive = librosa.decompose.hpss(S)
    harm_mag  = np.abs(harmonic)
    perc_mag  = np.abs(percussive)
    soft_mask = harm_mag / (harm_mag + perc_mag + 1e-6)
    soft_mask = librosa.decompose.nn_filter(soft_mask, aggregate=np.mean, metric='cosine')
    blend     = 0.3
    mask_final = (1 - blend) + blend * soft_mask
    S_final    = S * mask_final 
    enhanced_audio = librosa.istft(S_final, hop_length=256, length=len(audio))

    # Step 4: Presence boost + volume match
    enhanced_audio = np.tanh(enhanced_audio * 1.2)
    enhanced_audio = enhanced_audio / (np.max(np.abs(enhanced_audio)) + 1e-6)
    rms_o = np.sqrt(np.mean(audio**2))
    rms_e = np.sqrt(np.mean(enhanced_audio**2))
    if rms_e > 0:
        enhanced_audio *= (rms_o / rms_e)
    enhanced_audio = np.clip(enhanced_audio, -1.0, 1.0)

    # Band signals
    filtered_signals = {}
    for name, (low, high) in bands.items():
        try:
            f = bandpass(enhanced_audio, low, high)
            f = f / (np.max(np.abs(f)) + 1e-6)
        except Exception:
            f = np.zeros_like(enhanced_audio)
        filtered_signals[name] = f

    # ---- UPDATE ALL GRAPHS ----
    time_original = np.linspace(0, len(audio) / sr, len(audio))
    time_clean    = np.linspace(0, len(enhanced_audio) / sr, len(enhanced_audio))

    fft_data = np.abs(np.fft.rfft(enhanced_audio))
    freqs    = np.fft.rfftfreq(len(enhanced_audio), 1 / sr)

    # Graph 1: Original
    ax1.cla()
    ax1.plot(time_original, audio, color='steelblue')
    ax1.set_title("Original (Recorded Voice + Noise)", color='white')
    ax1.set_facecolor('#1a1a2e')
    ax1.tick_params(colors='gray')

    # Graph 2: Enhanced
    ax2.cla()
    ax2.plot(time_clean, enhanced_audio, color='limegreen')
    ax2.set_title("After Smart Voice Isolation (Natural & Clear)", color='white')
    ax2.set_facecolor('#1a1a2e')
    ax2.tick_params(colors='gray')

    # Graph 3: Spectrum
    ax3.cla()
    ax3.plot(freqs, fft_data, color='black', alpha=0.6)
    ax3.set_xlim(0, sr // 2)
    ax3.set_title("Enhanced Voice Spectrum", color='white')
    ax3.set_facecolor('#1a1a2e')
    ax3.tick_params(colors='gray')

    title_obj.set_text("✅ Done! Press buttons below to play.")
    fig.canvas.draw_idle()
    print("Processing Completed ✅")

# =============================
# FIGURE  (same layout as original — 3 subplots)
# =============================
fig = plt.figure(figsize=(14, 10), facecolor='#0d0d0d')
fig.subplots_adjust(top=0.88, bottom=0.12, hspace=0.45)

title_obj = fig.suptitle("🎙 Press RECORD to start", fontsize=14,
                          color='yellow', fontweight='bold')

ax1 = plt.subplot(3, 1, 1)
ax2 = plt.subplot(3, 1, 2)
ax3 = plt.subplot(3, 1, 3)

for ax, ttl in [
    (ax1, "Original (Recorded Voice + Noise)"),
    (ax2, "After Smart Voice Isolation (Natural & Clear)"),
    (ax3, "Enhanced Voice Spectrum"),
]:
    ax.set_facecolor('#1a1a2e')
    ax.set_title(ttl, color='white', fontsize=9)
    ax.tick_params(colors='gray')
    for sp in ax.spines.values():
        sp.set_edgecolor('#333')

# Live waveform line in ax1 (shown while recording)
t_live   = np.linspace(0, 3, sr * 3)
line_live, = ax1.plot(t_live, live_buffer, color='tomato', lw=0.7)
ax1.set_xlim(0, 3)
ax1.set_ylim(-1, 1)

# =============================
# ANIMATION — live rolling buffer
# =============================
def animate(_):
    global live_buffer
    if not is_recording:
        return (line_live,)

    chunks = []
    try:
        while True:
            chunks.append(audio_queue.get_nowait())
    except queue.Empty:
        pass

    if chunks:
        new_data = np.concatenate(chunks)
        n = len(new_data)
        if n >= len(live_buffer):
            live_buffer = new_data[-len(live_buffer):]
        else:
            live_buffer = np.roll(live_buffer, -n)
            live_buffer[-n:] = new_data
        line_live.set_ydata(live_buffer)

    return (line_live,)

ani = animation.FuncAnimation(fig, animate, interval=50,
                               blit=True, cache_frame_data=False)

# =============================
# RECORDING THREAD
# =============================
def do_record():
    global is_recording, live_buffer

    live_buffer[:] = 0
    while not audio_queue.empty():
        try: audio_queue.get_nowait()
        except queue.Empty: break

    is_recording = True
    title_obj.set_text("🔴 Recording… (10 seconds) – speak now!")
    ax1.set_xlim(0, 3)
    ax1.set_ylim(-1, 1)
    fig.canvas.draw_idle()

    collected = []

    def callback(indata, frames, time_info, status_flag):
        chunk = indata[:, 0].copy()
        collected.append(chunk)
        audio_queue.put(chunk)

    with sd.InputStream(samplerate=sr, channels=1,
                        blocksize=CHUNK, dtype='float32',
                        callback=callback):
        sd.sleep(int(duration * 1000))

    is_recording = False

    if not collected:
        title_obj.set_text("❌ No audio captured! Check microphone.")
        fig.canvas.draw_idle()
        return

    title_obj.set_text("⚙️ Processing… please wait")
    fig.canvas.draw_idle()

    raw = np.concatenate(collected).astype(np.float32)
    process_and_update(raw)

# =============================
# BUTTON CALLBACKS  (same as original + record)
# =============================
def btn_record(_):
    if not is_recording:
        threading.Thread(target=do_record, daemon=True).start()

def make_callback(name):
    def callback(event):
        if name in filtered_signals:
            sd.stop()
            sd.play(filtered_signals[name].astype(np.float32), sr)
    return callback

def play_original(event):
    if audio is not None:
        sd.stop()
        sd.play(audio.astype(np.float32), sr)

def stop_audio(event):
    sd.stop()

# =============================
# BUTTONS  (same positions as original, RECORD added at far left)
# =============================
button_width  = 0.09
button_height = 0.05
y_position    = 0.01

# 🎙 RECORD button  — new addition
ax_rec = plt.axes([0.01, y_position, button_width, button_height])
btn_rec = Button(ax_rec, "🎙 RECORD", color='#c0392b', hovercolor='#922b21')
btn_rec.label.set_color('white')
btn_rec.label.set_fontsize(8)
btn_rec.on_clicked(btn_record)

buttons = [btn_rec]

# Band buttons  (same as original, shifted slightly right)
for i, name in enumerate(bands.keys()):
    ax_button = plt.axes([0.12 + i * 0.13, y_position, button_width, button_height])
    btn = Button(ax_button, name.split()[0])
    btn.on_clicked(make_callback(name))
    buttons.append(btn)

# Original + Stop  (same as original)
ax_original = plt.axes([0.65, y_position, button_width, button_height])
btn_original = Button(ax_original, "Original")
btn_original.on_clicked(play_original)
buttons.append(btn_original)

ax_stop = plt.axes([0.76, y_position, button_width, button_height])
btn_stop = Button(ax_stop, "STOP")
btn_stop.on_clicked(stop_audio)
buttons.append(btn_stop)

plt.show()