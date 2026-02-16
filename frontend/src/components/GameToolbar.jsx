import React from 'react';
import itemsSprite from '../assets/pixel-dungeon/sprites/items.png';

// Helper to get sprite coords (copied from App.jsx, usually this should be in a utility file)
// But for now, I'll include it here or import it if I extract it.
// I will extract it to a utility file later, for now I'll duplicate to ensure it works then refactor.
const ITEM_SPRITES = {
    // Weapon Tier 1
    "Shortsword": [13, 13],
    "Mage's Staff": [15, 16],
    "Dagger": [12, 13],
    "Spirit Bow": [0, 10],

    // Weapon Tier 2
    "Wooden Club": [15, 15],
    "Spear": [0, 7],

    // Wearable
    "Cloth Armor": [15, 12],
    "Leather Vest": [14, 13],
    "Rogue's Cloak": [9, 15],
    "Broken Shield": [12, 16],

    // Potions
    "Potion": [12, 14],

    // Default
    "default": [8, 13],

    // Throwables
    "Stone": [10, 10],
    "Boomerang": [11, 10],
    "Throwable Dagger": [12, 13]
};

const getItemSpriteCoords = (itemName, itemType) => {
    for (const key in ITEM_SPRITES) {
        if (itemName && itemName.includes(key)) {
            return ITEM_SPRITES[key];
        }
    }
    if (itemType === 'potion') return [12, 14];
    if (itemType === 'weapon') return [14, 14];
    if (itemType === 'wearable') return [14, 12];

    if (itemType === 'throwable') return [11, 10];
    return ITEM_SPRITES["default"];
}

const GameToolbar = ({ inventory, equippedWeapon, targetingMode, onToggleInventory, onToolbarClick, onToolbarDoubleClick, messages }) => {
    // Calculate toolbar items (first 5 items)
    const toolbarItems = Array.from({ length: 5 }).map((_, i) => inventory[i] || null);

    return (
        <div className="game-hud-bottom">
            <div className="toolbar-container">
                <div className="toolbar">
                    {toolbarItems.map((item, i) => {
                        const spriteCoords = item ? getItemSpriteCoords(item.name, item.type) : null;
                        return (
                            <div
                                key={i}
                                className={`toolbar-slot ${targetingMode && equippedWeapon?.id === item?.id ? 'targeting-active' : ''}`}
                                onClick={() => onToolbarClick(item)}
                                onDoubleClick={() => onToolbarDoubleClick(item)}
                            >
                                {item ? (
                                    <>
                                        <div className="toolbar-item-sprite">
                                            <div style={{
                                                width: '16px',
                                                height: '16px',
                                                backgroundImage: `url(${itemsSprite})`,
                                                backgroundPosition: `-${spriteCoords[0] * 16}px -${spriteCoords[1] * 16}px`,
                                                transform: 'scale(2)',
                                                transformOrigin: 'top left',
                                                imageRendering: 'pixelated'
                                            }}></div>
                                        </div>
                                        <div className="toolbar-item-name">{item.name.substring(0, 8)}..</div>
                                    </>
                                ) : <span className="slot-number">{i + 1}</span>}
                            </div>
                        );
                    })}
                </div>

                <button className="inventory-toggle-btn-bottom" onClick={onToggleInventory}>
                    🎒
                </button>
            </div>

            <div className="connection-log">
                {messages.slice(-3).map((msg, i) => (
                    <div key={i} className="log-entry">{msg}</div>
                ))}
            </div>
        </div>
    );
};

export default GameToolbar;
