import { useState } from 'react';
import Navbar from './components/Navbar';
import TabContainer from './components/TabContainer';
import Tab1_ReadDocument from './components/Tab1_ReadDocument';
import Tab2_Translate from './components/Tab2_Translate';
import Tab3_FAQBot from './components/Tab3_FAQBot';

const TABS = [
  { id: 'read', label: 'Read document' },
  { id: 'translate', label: 'Translate' },
  { id: 'faq', label: 'Ask a question' },
];

export default function App() {
  const [active, setActive] = useState('read');

  return (
    <div className="app">
      <Navbar />
      <main className="container">
        <TabContainer tabs={TABS} active={active} onChange={setActive} />
        {/* Hidden instead of unmounted, so each tab keeps its work */}
        <div hidden={active !== 'read'}><Tab1_ReadDocument /></div>
        <div hidden={active !== 'translate'}><Tab2_Translate /></div>
        <div hidden={active !== 'faq'}><Tab3_FAQBot /></div>
      </main>
    </div>
  );
}
