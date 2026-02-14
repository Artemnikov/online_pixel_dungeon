class AudioManager {
    constructor() {
        this.audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        this.sounds = {};
        this.enabled = true;
    }

    play(soundName) {
        if (!this.enabled) return;
        if (this.audioCtx.state === 'suspended') {
            this.audioCtx.resume();
        }

        switch (soundName) {
            case 'MOVE':
                this.playTone(200, 'sine', 0.05, 0.1);
                break;
            case 'ATTACK':
                this.playTone(100, 'sawtooth', 0.1, 0.3); // aggressive sound
                this.playTone(150, 'sawtooth', 0.1, 0.3, 0.05);
                break;
            case 'DAMAGE':
                this.playTone(100, 'square', 0.2, 0.3);
                this.playTone(80, 'square', 0.2, 0.3, 0.1);
                break;
            case 'DEATH':
                this.playTone(150, 'sawtooth', 0.5, 0.5);
                this.playTone(100, 'sawtooth', 0.5, 0.5, 0.2);
                this.playTone(50, 'sawtooth', 0.8, 0.8, 0.4);
                break;
            case 'PICKUP':
                this.playTone(400, 'sine', 0.1, 0.1);
                this.playTone(600, 'sine', 0.1, 0.1, 0.05);
                break;
            case 'DRINK':
                this.playTone(300, 'triangle', 0.1, 0.1);
                this.playTone(350, 'triangle', 0.1, 0.1, 0.1);
                this.playTone(400, 'triangle', 0.2, 0.2, 0.2);
                break;
            case 'STAIRS_DOWN':
                this.playTone(200, 'sine', 0.5, 0.5);
                this.playTone(150, 'sine', 0.5, 0.5, 0.2);
                this.playTone(100, 'sine', 0.5, 0.5, 0.4);
                break;
            case 'REVIVE':
                this.playTone(300, 'sine', 0.5, 0.5);
                this.playTone(400, 'sine', 0.5, 0.5, 0.2);
                this.playTone(500, 'sine', 0.5, 0.5, 0.4);
                break;
            default:
                console.log(`Sound not found: ${soundName}`);
        }
    }

    playTone(freq, type, duration, vol, delay = 0) {
        const osc = this.audioCtx.createOscillator();
        const gain = this.audioCtx.createGain();

        osc.type = type;
        osc.frequency.setValueAtTime(freq, this.audioCtx.currentTime + delay);

        gain.gain.setValueAtTime(vol, this.audioCtx.currentTime + delay);
        gain.gain.exponentialRampToValueAtTime(0.01, this.audioCtx.currentTime + delay + duration);

        osc.connect(gain);
        gain.connect(this.audioCtx.destination);

        osc.start(this.audioCtx.currentTime + delay);
        osc.stop(this.audioCtx.currentTime + delay + duration);
    }
}

export default new AudioManager();
