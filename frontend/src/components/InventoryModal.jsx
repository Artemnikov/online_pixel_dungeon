import React from 'react';

const InventoryModal = ({ inventory, onClose, onUse, onEquip, onDrop }) => {
    return (
        <div className="inventory-overlay">
            <div className="inventory-modal">
                <div className="inventory-header">
                    <h2>Inventory (20 slots)</h2>
                    <button className="close-btn" onClick={onClose}>×</button>
                </div>
                <div className="inventory-grid">
                    {inventory.map((item, i) => (
                        <div key={item.id || i} className="inventory-slot">
                            <div className="item-name">{item.name}</div>
                            <div className="item-type">{item.type}</div>
                            <div className="item-stats">
                                {item.type === 'weapon' ? `Dmg: ${item.damage}` : (item.health_boost ? `HP+: ${item.health_boost}` : '')}
                                {item.type === 'potion' && item.effect === 'regen' && 'Regen 50% HP'}
                                {item.type === 'potion' && item.effect === 'revive' && 'Revives DBNO Ally'}
                            </div>
                            <div className="item-actions">
                                {item.type === 'potion' && (
                                    <button className="use-btn" onClick={() => onUse(item.id)}>Drink</button>
                                )}
                                {item.type !== 'potion' && (
                                    <button onClick={() => onEquip(item.id)}>Equip</button>
                                )}
                                <button onClick={() => onDrop(item.id)}>Drop</button>
                            </div>
                        </div>
                    ))}
                    {Array.from({ length: 20 - inventory.length }).map((_, i) => (
                        <div key={`empty-${i}`} className="inventory-slot empty"></div>
                    ))}
                </div>
            </div>
        </div>
    );
};

export default InventoryModal;
