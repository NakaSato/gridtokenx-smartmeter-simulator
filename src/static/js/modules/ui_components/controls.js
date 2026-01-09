// Button States
export function updateButtonStates(status) {
    const startBtn = document.getElementById('start-btn');
    const stopBtn = document.getElementById('stop-btn');
    const pauseBtn = document.getElementById('pause-btn');
    const resumeBtn = document.getElementById('resume-btn');
    const updateBtn = document.getElementById('update-meters-btn');
    const meterCountInput = document.getElementById('meter-count');

    if (status.running) {
        // Running state
        if (startBtn) startBtn.disabled = true;
        if (stopBtn) stopBtn.disabled = false;
        if (updateBtn) updateBtn.disabled = true;
        if (meterCountInput) meterCountInput.disabled = true;

        if (status.paused) {
            // Paused state
            if (pauseBtn) {
                pauseBtn.disabled = true;
                pauseBtn.classList.add('hidden');
            }
            if (resumeBtn) {
                resumeBtn.disabled = false;
                resumeBtn.classList.remove('hidden');
            }
        } else {
            // Normal running state
            if (pauseBtn) {
                pauseBtn.disabled = false;
                pauseBtn.classList.remove('hidden');
            }
            if (resumeBtn) {
                resumeBtn.disabled = true;
                resumeBtn.classList.add('hidden');
            }
        }
    } else {
        // Stopped state
        if (startBtn) startBtn.disabled = false;
        if (stopBtn) stopBtn.disabled = true;
        if (pauseBtn) {
            pauseBtn.disabled = true;
            pauseBtn.classList.add('hidden');
        }
        if (resumeBtn) {
            resumeBtn.disabled = true;
            resumeBtn.classList.add('hidden');
        }
        if (updateBtn) updateBtn.disabled = false;
        if (meterCountInput) meterCountInput.disabled = false;
    }

    // Update meter count display
    if (status.num_meters && meterCountInput) {
        meterCountInput.value = status.num_meters;
    }
}
