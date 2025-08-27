import { useEffect } from 'react';

export interface KeyboardShortcut {
    key: string;
    callback: () => void;
    description: string;
    preventDefault?: boolean;
}

export function useKeyboardShortcuts(shortcuts: KeyboardShortcut[], enabled: boolean = true) {
    useEffect(() => {
        if (!enabled) return;

        const handleKeyPress = (event: KeyboardEvent) => {
            // Don't trigger shortcuts when typing in input fields
            if (
                event.target instanceof HTMLInputElement ||
                event.target instanceof HTMLTextAreaElement
            ) {
                return;
            }

            const shortcut = shortcuts.find((s) => s.key.toLowerCase() === event.key.toLowerCase());
            if (shortcut) {
                if (shortcut.preventDefault !== false) {
                    event.preventDefault();
                }
                shortcut.callback();
            }
        };

        window.addEventListener('keydown', handleKeyPress);
        return () => window.removeEventListener('keydown', handleKeyPress);
    }, [shortcuts, enabled]);
}

export function formatKeyboardShortcut(key: string): string {
    const keyMap: Record<string, string> = {
        ' ': 'Space',
        arrowleft: '←',
        arrowright: '→',
        arrowup: '↑',
        arrowdown: '↓',
        enter: 'Enter',
        escape: 'Esc',
    };

    return keyMap[key.toLowerCase()] || key.toUpperCase();
}
