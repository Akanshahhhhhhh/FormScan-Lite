import { useState } from 'react';
import Navbar from './components/Navbar';
import TabContainer from './components/TabContainer';
import LanguagePicker from './components/LanguagePicker';
import Tab1_ReadDocument from './components/Tab1_ReadDocument';
import Tab2_Translate from './components/Tab2_Translate';
import Tab3_FAQBot from './components/Tab3_FAQBot';
import { useLang } from './i18n/LanguageContext';

export default function App() {
  const { t, chosen, pickerOpen } = useLang();
  const [active, setActive] = useState('read');

  // First launch: only the language picker
  if (!chosen) return <LanguagePicker />;

  const tabs = [
    { id: 'read', label: t('tab.read') },
    { id: 'translate', label: t('tab.translate') },
    { id: 'faq', label: t('tab.faq') },
  ];

  return (
    <div className="app">
      <Navbar />
      <main className="container">
        <TabContainer tabs={tabs} active={active} onChange={setActive} />
        {/* Hidden instead of unmounted, so each tab keeps its work */}
        <div hidden={active !== 'read'}><Tab1_ReadDocument /></div>
        <div hidden={active !== 'translate'}><Tab2_Translate /></div>
        <div hidden={active !== 'faq'}><Tab3_FAQBot /></div>
      </main>
      {pickerOpen && <LanguagePicker />}
    </div>
  );
}
