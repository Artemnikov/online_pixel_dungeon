import { useEffect, useRef } from 'react';

export const useGameInput = (sendAction, inventory, handleToolbarClick, handleToolbarDoubleClick, setShowInventory) => {
    const lastKeyRef = useRef({ key: null, time: 0 });

    useEffect(() => {
        const handleKeyDown = (e) => {
            if (e.key === 'f') {
                setShowInventory(prev => !prev);
                return;
            }

            let direction = null;
            if (e.key === 'ArrowUp' || e.key === 'w') direction = 'UP';
            if (e.key === 'ArrowDown' || e.key === 's') direction = 'DOWN';
            if (e.key === 'ArrowLeft' || e.key === 'a') direction = 'LEFT';
            if (e.key === 'ArrowRight' || e.key === 'd') direction = 'RIGHT';

            // Toolbar hotkeys 1-5
            if (['1', '2', '3', '4', '5'].includes(e.key)) {
                const index = parseInt(e.key) - 1;
                const item = inventory[index];
                if (item) {
                    const now = Date.now();
                    const isDoubleTap = lastKeyRef.current.key === e.key && (now - lastKeyRef.current.time) < 300;

                    if (isDoubleTap) {
                        handleToolbarDoubleClick(item);
                        lastKeyRef.current = { key: null, time: 0 }; // Reset
                    } else {
                        handleToolbarClick(item);
                        lastKeyRef.current = { key: e.key, time: now };
                    }
                }
            }

            if (direction) {
                sendAction({ type: 'MOVE', direction });
            }
        }

        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [inventory, handleToolbarClick, handleToolbarDoubleClick, sendAction, setShowInventory]);
};
