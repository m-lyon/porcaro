import { StrictMode } from 'react';
import { BrowserRouter } from 'react-router';
import { createRoot } from 'react-dom/client';
import { Toaster } from '@porcaro/components/ui/sonner';

import './index.css';
import App from './App';

const rootElement = document.getElementById('root');
if (!rootElement) throw new Error('Root element not found');

createRoot(rootElement).render(
    <StrictMode>
        <BrowserRouter>
            <App />
            <Toaster />
        </BrowserRouter>
    </StrictMode>
);
