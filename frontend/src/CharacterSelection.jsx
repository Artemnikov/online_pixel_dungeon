import React, { useState } from 'react';
import warriorArt from './assets/pixel-dungeon/art/warrior.png';
import mageArt from './assets/pixel-dungeon/art/mage.png';
import rogueArt from './assets/pixel-dungeon/art/rogue.png';
import huntressArt from './assets/pixel-dungeon/art/huntress.png';

const CharacterSelection = ({ onSelect }) => {
  const [selectedClass, setSelectedClass] = useState('warrior');

  const classes = [
    { id: 'warrior', name: 'Warrior', art: warriorArt, desc: 'Starts with a Shortsword and Cloth Armor.' },
    { id: 'mage', name: 'Mage', art: mageArt, desc: 'Starts with a Magic Staff (4 charges).' },
    { id: 'rogue', name: 'Rogue', art: rogueArt, desc: 'Starts with a Dagger and Cloak.' },
    { id: 'huntress', name: 'Archer', art: huntressArt, desc: 'Starts with a Spirit Bow.' },
  ];

  return (
    <div className="character-selection-screen">
      <h1>Select Your Hero</h1>
      <div className="classes-container">
        {classes.map((c) => (
          <div
            key={c.id}
            className={`class-card ${selectedClass === c.id ? 'selected' : ''}`}
            onClick={() => setSelectedClass(c.id)}
          >
            <div className="art-preview">
              <img src={c.art} alt={c.name} style={{ width: '100%', height: 'auto', borderRadius: '4px' }} />
            </div>
            <h3>{c.name}</h3>
            <p>{c.desc}</p>
          </div>
        ))}
      </div>
      <button className="start-btn" onClick={() => onSelect(selectedClass)}>
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
        .classes-container {
          display: flex;
          gap: 20px;
          margin: 40px 0;
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
