import { Routes, Route } from 'react-router';
import HomePage from './pages/HomePage';
import SessionPage from './pages/SessionPage';
import LabelingPage from './pages/LabelingPage';
import './App.css';

function App() {
    return (
        <div className='min-h-screen bg-background'>
            <header className='border-b'>
                <div className='container mx-auto px-4 py-4'>
                    <h1 className='text-2xl font-bold text-foreground'>
                        Porcaro - Drum Transcription Data Labeling
                    </h1>
                    <p className='text-muted-foreground mt-1'>
                        Train machine learning models for automatic drum transcription
                    </p>
                </div>
            </header>

            <main className='container mx-auto px-4 py-8'>
                <Routes>
                    <Route path='/' element={<HomePage />} />
                    <Route path='/session/:sessionId' element={<SessionPage />} />
                    <Route path='/session/:sessionId/label' element={<LabelingPage />} />
                </Routes>
            </main>
        </div>
    );
}

export default App;
