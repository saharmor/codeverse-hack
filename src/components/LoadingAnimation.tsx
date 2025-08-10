'use client'

import React, { useState, useEffect } from 'react'
import { 
  Bot, 
  BookOpen, 
  Code2, 
  FileText, 
  MessageSquare
} from 'lucide-react'

interface LoadingAnimationProps {
  isVisible: boolean
}

const loadingMessages = [
  "Deploying agents...",
  "Reading repository context...",
  "Analyzing code structure...",
  "Generating implementation plan...",
  "Preparing response..."
]

const messageIcons = [
  { icon: Bot, color: "text-purple-600", description: "AI Agent" },
  { icon: BookOpen, color: "text-blue-600", description: "Repository" },
  { icon: Code2, color: "text-green-600", description: "Code Analysis" },
  { icon: FileText, color: "text-orange-600", description: "Planning" },
  { icon: MessageSquare, color: "text-pink-600", description: "Response" }
]

export default function LoadingAnimation({ isVisible }: LoadingAnimationProps) {
  const [currentMessageIndex, setCurrentMessageIndex] = useState(0)

  useEffect(() => {
    if (!isVisible) return

    const messageInterval = setInterval(() => {
      setCurrentMessageIndex(prev => (prev + 1) % loadingMessages.length)
    }, 2000)

    return () => {
      clearInterval(messageInterval)
    }
  }, [isVisible])

  if (!isVisible) return null

  const CurrentIcon = messageIcons[currentMessageIndex].icon
  const iconColor = messageIcons[currentMessageIndex].color

  return (
    <div className="flex items-start gap-3">
      <div className="w-8 h-8 rounded-full bg-purple-600 flex items-center justify-center text-white text-sm font-medium">
        AI
      </div>
      <div className="max-w-[70%] rounded-2xl px-4 py-3 bg-gray-50 border border-gray-200 shadow-sm">
        <div className="flex items-center gap-3">
          {/* Bouncing Icon */}
          <div 
            className={`${iconColor} filter drop-shadow-sm`}
            style={{ 
              animation: 'icon-bounce 2s infinite ease-in-out'
            }}
          >
            <CurrentIcon className="w-5 h-5" />
          </div>
          
          {/* Loading Message */}
          <span className="text-sm text-gray-600 font-medium">
            {loadingMessages[currentMessageIndex]}
          </span>
        </div>
      </div>
    </div>
  )
}
