import { BrowserRouter, Routes, Route } from "react-router-dom";
import { EntrancePage } from "./pages/EntrancePage";
import { ReadingPage } from "./pages/ReadingPage";
import { CardDatabasePage } from "./pages/CardDatabasePage";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<EntrancePage />} />
        <Route path="/player/:tag" element={<ReadingPage />} />
        <Route path="/cards" element={<CardDatabasePage />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
