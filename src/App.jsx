import { Route, Routes } from 'react-router-dom';
import Home from './pages/Home';
import Voice from './pages/Voice';
import History from './pages/History';
import About from './pages/About';
import NotFound from './pages/NotFound';

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Home />} />
      <Route path="/voice" element={<Voice />} />
      <Route path="/history" element={<History />} />
      <Route path="/about" element={<About />} />
      <Route path="*" element={<NotFound />} />
    </Routes>
  );
}
