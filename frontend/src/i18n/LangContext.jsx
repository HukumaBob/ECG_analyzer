import { createContext, useContext, useState } from 'react'
import ru from './ru.js'
import en from './en.js'

const STRINGS = { ru, en }

const LangContext = createContext(null)

export function LangProvider({ children }) {
  const [lang, setLang] = useState('ru')
  const t = STRINGS[lang]
  const toggle = () => setLang(l => l === 'ru' ? 'en' : 'ru')
  return (
    <LangContext.Provider value={{ lang, t, toggle }}>
      {children}
    </LangContext.Provider>
  )
}

export function useLang() {
  return useContext(LangContext)
}
