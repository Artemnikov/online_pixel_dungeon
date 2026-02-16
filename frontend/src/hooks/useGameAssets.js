import { useState, useEffect } from 'react';
import sewerTiles from '../assets/pixel-dungeon/environment/tiles_sewers.png';
import warriorSprite from '../assets/pixel-dungeon/sprites/warrior.png';
import mageSprite from '../assets/pixel-dungeon/sprites/mage.png';
import rogueSprite from '../assets/pixel-dungeon/sprites/rogue.png';
import huntressSprite from '../assets/pixel-dungeon/sprites/huntress.png';
import itemsSprite from '../assets/pixel-dungeon/sprites/items.png';
import ratSprite from '../assets/pixel-dungeon/sprites/rat.png';
import batSprite from '../assets/pixel-dungeon/sprites/bat.png';

export const useGameAssets = () => {
    const [assetImages, setAssetImages] = useState({
        tiles: null,
        warrior: null,
        mage: null,
        rogue: null,
        huntress: null,
        items: null,
        rat: null,
        bat: null,
    });

    useEffect(() => {
        const loadImage = (src, key) => {
            const img = new Image();
            img.src = src;
            img.onload = () => {
                setAssetImages(prev => ({ ...prev, [key]: img }));
            };
        }

        loadImage(sewerTiles, 'tiles');
        loadImage(warriorSprite, 'warrior');
        loadImage(mageSprite, 'mage');
        loadImage(rogueSprite, 'rogue');
        loadImage(huntressSprite, 'huntress');
        loadImage(itemsSprite, 'items');
        loadImage(ratSprite, 'rat');
        loadImage(batSprite, 'bat');
    }, []);

    return assetImages;
};
