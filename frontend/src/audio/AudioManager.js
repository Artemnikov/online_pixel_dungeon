import atkBowSound from '../assets/pixel-dungeon/audio/atk_bow.mp3';
import zapSound from '../assets/pixel-dungeon/audio/zap.mp3';
import hitMagicSound from '../assets/pixel-dungeon/audio/hit_magic.mp3';

class AudioManager {
    constructor() {
        this.audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        this.sounds = {};
        this.enabled = true;
        this.loadedSounds = {};

        this.loadSound('ATTACK_BOW', atkBowSound);
        this.loadSound('ATTACK_MAGIC', zapSound);
        this.loadSound('HIT_MAGIC', hitMagicSound);
    }

    async loadSound(name, src) {
        try {
            const response = await fetch(src);
            const arrayBuffer = await response.arrayBuffer();
            const audioBuffer = await this.audioCtx.decodeAudioData(arrayBuffer);
            this.loadedSounds[name] = audioBuffer;
        } catch (e) {
            console.error(`Failed to load sound ${name}:`, e);
        }
    }

    play(soundName) {
        if (!this.enabled) return;
        if (this.audioCtx.state === 'suspended') {
            this.audioCtx.resume();
        }

        if (this.loadedSounds[soundName]) {
            this.playSoundBuffer(this.loadedSounds[soundName]);
            return;
        }

        // Fallback to synthesized sounds for unmatched names
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
                // console.log(`Sound not found: ${soundName}`);
                break;
        }
    }

    playStep(tileType) {
        if (!this.enabled) return;

        // tileType: 2 = FLOOR (Generic), 6 = WOOD, 7 = WATER, 8 = COBBLE
        // Using synthesis for now

        // Randomize pitch slightly for realism
        const detune = (Math.random() - 0.5) * 50;

        if (tileType === 7) { // WATER
            // Splashy sound
            this.playNoise(0.1, 0.2, 'lowpass', 400);
        } else if (tileType === 6) { // WOOD
            // Hollow woody tap
            this.playTone(300 + detune, 'square', 0.05, 0.1);
        } else if (tileType === 8) { // COBBLE
            // Hard click
            this.playTone(400 + detune, 'triangle', 0.05, 0.15);
        } else { // Generic Floor
            this.playTone(200 + detune, 'sine', 0.05, 0.1);
        }
    }

    playNoise(duration, vol, filterType, filterFreq) {
        const bufferSize = this.audioCtx.sampleRate * duration;
        const buffer = this.audioCtx.createBuffer(1, bufferSize, this.audioCtx.sampleRate);
        const data = buffer.getChannelData(0);

        for (let i = 0; i < bufferSize; i++) {
            data[i] = Math.random() * 2 - 1;
        }

        const noise = this.audioCtx.createBufferSource();
        noise.buffer = buffer;

        const gain = this.audioCtx.createGain();
        gain.gain.setValueAtTime(vol, this.audioCtx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.01, this.audioCtx.currentTime + duration);

        if (filterType) {
            const filter = this.audioCtx.createBiquadFilter();
            filter.type = filterType;
            filter.frequency.value = filterFreq;
            noise.connect(filter);
            filter.connect(gain);
        } else {
            noise.connect(gain);
        }

        gain.connect(this.audioCtx.destination);
        noise.start();
    }

    playSoundBuffer(buffer) {
        const source = this.audioCtx.createBufferSource();
        source.buffer = buffer;
        source.connect(this.audioCtx.destination);
        source.start(0);
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
