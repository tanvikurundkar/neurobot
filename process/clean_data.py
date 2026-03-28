 
import os
import numpy as np
import matplotlib.pyplot as plt
import mne
from mne_bids import BIDSPath, read_raw_bids
from mne.preprocessing import ICA
 

BIDS_ROOT = "./data/ds004368"
OUTPUT_DIR = "./data/cleaned"
TASK = "rest"
 
# filter stuff
LOW = 1.0
HIGH = 40.0
NOTCH = 60.0  # powerline noise in US is 60hz
 
# ica settings
N_COMPONENTS = 20
 
# epoch window
TMIN = 0.0
TMAX = 1.0
 
 
# loads the raw eeg file for a subject
def load_subject(subject):
    print("loading subject: " + subject)
 
    path = BIDSPath(
        subject=subject,
        task=TASK,
        datatype="eeg",
        root=BIDS_ROOT
    )
 
    raw = read_raw_bids(bids_path=path, verbose=False)
    raw.load_data()
 
    # just printing some info to make sure it loaded right
    print("num channels: " + str(len(raw.ch_names)))
    print("duration: " + str(raw.times[-1]) + " seconds")
    print("sample rate: " + str(raw.info['sfreq']) + " Hz")
 
    return raw
 
 
# apply bandpass and notch filter to remove noise
def filter_data(raw):
    print("filtering...")
 
    # bandpass filter - removes anything below 1hz and above 40hz
    raw.filter(l_freq=LOW, h_freq=HIGH, verbose=False)
 
    # notch filter to remove 60hz powerline noise
    raw.notch_filter(freqs=NOTCH, verbose=False)
 
    return raw
 
 
# set average reference
def set_ref(raw):
    print("setting reference...")
    raw.set_eeg_reference("average", projection=True)
    raw.apply_proj()
    return raw
 
 
# try to find bad channels automatically
def find_bad_channels(raw):
    print("checking for bad channels...")
 
    data = raw.get_data(picks="eeg")
 
    # flat channels have basically no signal
    flat = np.std(data, axis=1) < 0.5e-6
    flat_list = [raw.ch_names[i] for i in range(len(flat)) if flat[i]]
 
    # noisy channels have way more variance than normal
    stds = np.std(data, axis=1)
    noisy = stds > 5 * np.median(stds)
    noisy_list = [raw.ch_names[i] for i in range(len(noisy)) if noisy[i]]
 
    bad = list(set(flat_list + noisy_list))
    raw.info["bads"] = bad
 
    print("bad channels found: " + str(bad))
 
    # interpolate them so we dont lose the data
    if len(bad) > 0:
        raw.interpolate_bads(reset_bads=True)
        print("interpolated bad channels")
 
    return raw
 
 
# run ICA to remove eye blinks and muscle artifacts
def run_ica(raw):
    print("running ICA... (this takes a while)")
 
    # need to highpass filter before ICA
    raw_copy = raw.copy().filter(1.0, None, verbose=False)
 
    ica = ICA(n_components=N_COMPONENTS, random_state=42, max_iter="auto")
    ica.fit(raw_copy, picks="eeg", verbose=False)
 
    # try to find eye blink components automatically
    eog_idx = []
    try:
        eog_idx, scores = ica.find_bads_eog(raw, verbose=False)
        print("eye artifact components: " + str(eog_idx))
    except:
        print("no channel found, skipping")
 
    ica.exclude = eog_idx
    ica.apply(raw)
    print("removed " + str(len(eog_idx)) + " components")
 
    return raw
 
 
# split data into epochs
def make_epochs(raw):
    print("making epochs...")
 
    events, event_id = mne.events_from_annotations(raw, verbose=False)
 
    # if no events found just split into 2 second chunks
    if len(events) == 0:
        print("no events found, using fixed length epochs")
        epochs = mne.make_fixed_length_epochs(raw, duration=2.0, preload=True, verbose=False)
    else:
        print("events: " + str(event_id))
        epochs = mne.Epochs(
            raw,
            events=events,
            event_id=event_id,
            tmin=TMIN,
            tmax=TMAX,
            baseline=(None, 0),
            reject=dict(eeg=150e-6),  # reject epochs with amplitude over 150 microvolts
            preload=True,
            verbose=False
        )
 
    print("kept " + str(len(epochs)) + " epochs")
    return epochs
 
 
# save the cleaned data
def save_data(epochs, subject):
    out_dir = os.path.join(OUTPUT_DIR, "sub-" + subject)
    os.makedirs(out_dir, exist_ok=True)
 
    filename = "sub-" + subject + "_cleaned-epo.fif"
    out_path = os.path.join(out_dir, filename)
    epochs.save(out_path, overwrite=True)
    print("saved to: " + out_path)
 
 
# save a plot of the power spectrum so we can check it looks right
def save_plot(epochs, subject):
    fig_dir = os.path.join(OUTPUT_DIR, "sub-" + subject + "_figures")
    os.makedirs(fig_dir, exist_ok=True)
 
    fig = epochs.plot_psd(fmin=1, fmax=40, show=False)
    fig_path = os.path.join(fig_dir, "sub-" + subject + "_psd.png")
    fig.savefig(fig_path)
    plt.close()
    print("saved plot to: " + fig_path)
 
 
# run everything for one subject
def process_one_subject(subject):
    print("\n--- processing sub-" + subject + " ---")
    raw = load_subject(subject)
    raw = filter_data(raw)
    raw = set_ref(raw)
    raw = find_bad_channels(raw)
    raw = run_ica(raw)
    epochs = make_epochs(raw)
    save_data(epochs, subject)
    save_plot(epochs, subject)
    print("done with sub-" + subject)
 
 
# get list of all subjects in the dataset folder
def get_subjects():
    subjects = []
    for folder in os.listdir(BIDS_ROOT):
        if folder.startswith("sub-"):
            subjects.append(folder.replace("sub-", ""))
    return sorted(subjects)
 
 
# main
if __name__ == "__main__":
    subjects = get_subjects()
    print("found " + str(len(subjects)) + " subjects")
 
    for sub in subjects:
        process_one_subject(sub)
 
    print("\nall done! files saved to: " + OUTPUT_DIR)