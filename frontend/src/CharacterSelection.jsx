import { useState, useRef, useEffect } from 'react';
import AudioManager from './audio/AudioManager';
import warriorArt from './assets/pixel-dungeon/art/warrior.png';
import themeMusic from './assets/pixel-dungeon/themes/theme_1.ogg';
import descendSound from './assets/pixel-dungeon/audio/descend.mp3';
import mageArt from './assets/pixel-dungeon/art/mage.png';
import rogueArt from './assets/pixel-dungeon/art/rogue.png';
import huntressArt from './assets/pixel-dungeon/art/huntress.png';

const CharacterSelection = ({ onSelect }) => {
  const [selectedClass, setSelectedClass] = useState('warrior');
  const [difficulty, setDifficulty] = useState('normal');
  const [playerName, setPlayerName] = useState('');
  const audioRef = useRef(null);
  const tryPlayRef = useRef(null);

  useEffect(() => {
    const audio = new Audio(themeMusic);
    audio.loop = true;
    audioRef.current = audio;
    let cancelled = false;

    const stopAudio = () => {
      audio.pause();
      audio.currentTime = 0;
    };

    const tryPlay = () => {
      const p = audio.play();
      if (p !== undefined) p.then(() => { if (cancelled) stopAudio(); }).catch(() => {});
    };
    tryPlayRef.current = tryPlay;

    const played = audio.play();
    if (played !== undefined) {
      played.then(() => {
        if (cancelled) stopAudio();
      }).catch(() => {
        document.addEventListener('click', tryPlay, { once: true });
        document.addEventListener('mousemove', tryPlay, { once: true });
      });
    }

    return () => {
      cancelled = true;
      if (played !== undefined) {
        played.then(stopAudio).catch(() => {});
      } else {
        stopAudio();
      }
      document.removeEventListener('click', tryPlay);
      document.removeEventListener('mousemove', tryPlay);
    };
  }, []);

  const classes = [
    { id: 'warrior', name: 'Warrior', art: warriorArt, desc: 'Starts with a Shortsword and Cloth Armor.' },
    { id: 'mage', name: 'Mage', art: mageArt, desc: 'Starts with a Magic Staff (4 charges).' },
    { id: 'rogue', name: 'Rogue', art: rogueArt, desc: 'Starts with a Dagger and Cloak.' },
    { id: 'huntress', name: 'Archer', art: huntressArt, desc: 'Starts with a Spirit Bow.' },
  ];

  return (
    <div className="character-selection-screen">
      <h1>Select Your Hero</h1>

      <div className="difficulty-container">
        <label>Difficulty: </label>
        <div className="difficulty-options">
          {['easy', 'normal', 'hard'].map(d => (
            <button
              key={d}
              className={`diff-btn ${difficulty === d ? 'active' : ''}`}
              onClick={() => { AudioManager.play('CLICK'); setDifficulty(d); }}
            >
              {d.toUpperCase()}
            </button>
          ))}
        </div>
      </div>

      <div className="classes-container">
        {classes.map((c) => (
          <div
            key={c.id}
            className={`class-card ${selectedClass === c.id ? 'selected' : ''}`}
            onClick={() => { AudioManager.play('CLICK'); setSelectedClass(c.id); }}
          >
            <div className="art-preview">
              <img src={c.art} alt={c.name} style={{ width: '100%', height: 'auto', borderRadius: '4px' }} />
            </div>
            <h3>{c.name}</h3>
            <p>{c.desc}</p>
          </div>
        ))}
      </div>
      <div className="name-container">
        <input
          className="name-input"
          type="text"
          placeholder="Enter your name (optional)"
          maxLength={20}
          value={playerName}
          onChange={e => setPlayerName(e.target.value)}
        />
      </div>

      <button className="start-btn" onClick={() => {
          AudioManager.play('CLICK');
          if (tryPlayRef.current) {
            document.removeEventListener('click', tryPlayRef.current);
            document.removeEventListener('mousemove', tryPlayRef.current);
          }
          if (audioRef.current) {
            audioRef.current.pause();
            audioRef.current.currentTime = 0;
          }
          new Audio(descendSound).play().catch(() => {});
          onSelect(selectedClass, difficulty, playerName.trim());
        }}>
        Enter Dungeon
      </button>

      <style jsx>{`
        .character-selection-screen {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          height: 100vh;
          background-color: #111;
          color: white;
          font-family: monospace;
        }
        .difficulty-container {
          display: flex;
          align-items: center;
          gap: 15px;
          margin-bottom: 20px;
          background: #222;
          padding: 10px 20px;
          border-radius: 8px;
          border: 1px solid #444;
        }
        .difficulty-options {
          display: flex;
          gap: 10px;
        }
        .diff-btn {
          background: #333;
          border: 1px solid #555;
          color: #888;
          padding: 5px 15px;
          cursor: pointer;
          border-radius: 4px;
          font-family: monospace;
        }
        .diff-btn.active {
          background: #e67e22;
          color: white;
          border-color: #d35400;
        }
        .classes-container {
          display: flex;
          gap: 20px;
          margin: 20px 0 40px 0;
        }
        .class-card {
          border: 2px solid #444;
          padding: 20px;
          border-radius: 8px;
          cursor: pointer;
          width: 200px;
          text-align: center;
          transition: all 0.2s;
        }
        .class-card:hover {
          background-color: #222;
        }
        .class-card.selected {
          border-color: #f1c40f;
          background-color: #222;
          box-shadow: 0 0 15px rgba(241, 196, 15, 0.3);
        }
        .name-container {
          margin-bottom: 20px;
        }
        .name-input {
          background: #222;
          border: 1px solid #555;
          color: white;
          padding: 8px 16px;
          border-radius: 4px;
          font-family: monospace;
          font-size: 16px;
          text-align: center;
          width: 260px;
          outline: none;
        }
        .name-input:focus {
          border-color: #f1c40f;
        }
        .start-btn {
          font-size: 24px;
          padding: 15px 40px;
          background-color: #27ae60;
          color: white;
          border: none;
          border-radius: 8px;
          cursor: pointer;
        }
        .start-btn:hover {
          background-color: #2ecc71;
        }
      `}</style>
    </div>
  );
};

export default CharacterSelection;
