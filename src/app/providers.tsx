'use client'

import React from 'react'
import { AppContextProvider } from '../lib/AppContext'

export function Providers({ children }: { children: React.ReactNode }) {
  return <AppContextProvider>{children}</AppContextProvider>
}
