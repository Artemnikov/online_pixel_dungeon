import React from 'react';

const GameHUD = ({ myStats }) => {
    return (
        <div className="top-left-hud">
            <div className="player-status-card">
                <div className="player-portrait">
                    {/* Simple placeholder or could be class sprite */}
                    <div className="portrait-inner">👤</div>
                </div>
                <div className="player-details">
                    <div className="player-name">{myStats.name}</div>
                    <div className="health-bar-container-large">
                        <div
                            className={`health-bar-fill-large ${myStats.isDowned ? 'downed' : myStats.isRegen ? 'regen' : ''}`}
                            style={{ width: `${(myStats.hp / myStats.maxHp) * 100}%` }}
                        ></div>
                        <div className="health-text-large">{Math.ceil(myStats.hp)} / {myStats.maxHp} HP</div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default GameHUD;
