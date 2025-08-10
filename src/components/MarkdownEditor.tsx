'use client'

import React, { useState, useCallback, useRef, useEffect } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import rehypeHighlight from 'rehype-highlight'
import 'highlight.js/styles/github.css'

interface MarkdownEditorProps {
  value?: string
  onChange?: (value: string) => void
  placeholder?: string
  className?: string
}

export default function MarkdownEditor({ 
  value = '', 
  onChange, 
  placeholder = 'Start writing your plan in markdown...',
  className = ''
}: MarkdownEditorProps) {
  const [content, setContent] = useState<string>(value)
  const [isEditing, setIsEditing] = useState(false)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    setContent(value)
  }, [value])

  const handleChange = useCallback((e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const newValue = e.target.value
    setContent(newValue)
    onChange?.(newValue)
  }, [onChange])

  const handleKeyDown = useCallback((e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Tab') {
      e.preventDefault()
      const textarea = textareaRef.current
      if (!textarea) return

      const start = textarea.selectionStart
      const end = textarea.selectionEnd
      const value = textarea.value

      if (e.shiftKey) {
        // Remove tab/spaces at beginning of lines
        const lines = value.substring(0, start).split('\n')
        const currentLine = lines[lines.length - 1]
        if (currentLine.startsWith('  ')) {
          const newValue = value.substring(0, start - 2) + value.substring(start)
          setContent(newValue)
          onChange?.(newValue)
          setTimeout(() => {
            textarea.selectionStart = textarea.selectionEnd = start - 2
          }, 0)
        }
      } else {
        // Add tab (2 spaces)
        const newValue = value.substring(0, start) + '  ' + value.substring(end)
        setContent(newValue)
        onChange?.(newValue)
        setTimeout(() => {
          textarea.selectionStart = textarea.selectionEnd = start + 2
        }, 0)
      }
    } else if (e.key === 'Escape') {
      setIsEditing(false)
      textareaRef.current?.blur()
    }
  }, [onChange])

  const handleClick = useCallback(() => {
    setIsEditing(true)
    setTimeout(() => {
      textareaRef.current?.focus()
    }, 0)
  }, [])

  const handleBlur = useCallback(() => {
    // Add a small delay to prevent flickering when clicking on the editor
    setTimeout(() => {
      if (document.activeElement !== textareaRef.current) {
        setIsEditing(false)
      }
    }, 100)
  }, [])

  if (!content && !isEditing) {
    return (
      <div 
        className={`w-full h-full flex flex-col ${className}`}
        onClick={handleClick}
      >
        <div className="flex-1 w-full p-4 text-gray-400 cursor-text">
          {placeholder}
        </div>
      </div>
    )
  }

  return (
    <div className={`w-full h-full flex flex-col relative ${className}`}>
      {isEditing ? (
        <textarea
          ref={textareaRef}
          value={content}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          onBlur={handleBlur}
          placeholder={placeholder}
          className="flex-1 w-full resize-none border-none outline-none p-4 font-mono text-sm leading-relaxed bg-white absolute inset-0 z-10"
          style={{
            fontFamily: 'ui-monospace, SFMono-Regular, "SF Mono", Consolas, "Liberation Mono", Menlo, monospace',
            fontSize: '14px',
            lineHeight: '1.6'
          }}
          spellCheck={false}
          autoFocus
        />
      ) : (
        <div 
          className="flex-1 w-full p-4 prose prose-sm max-w-none cursor-text overflow-y-auto"
          onClick={handleClick}
        >
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            rehypePlugins={[rehypeHighlight]}
            components={{
              h1: ({children}) => <h1 className="text-2xl font-bold mb-4 text-gray-900">{children}</h1>,
              h2: ({children}) => <h2 className="text-xl font-semibold mb-3 text-gray-900">{children}</h2>,
              h3: ({children}) => <h3 className="text-lg font-medium mb-2 text-gray-900">{children}</h3>,
              p: ({children}) => <p className="mb-4 text-gray-700 leading-relaxed">{children}</p>,
              ul: ({children}) => <ul className="mb-4 ml-6 space-y-1">{children}</ul>,
              ol: ({children}) => <ol className="mb-4 ml-6 space-y-1">{children}</ol>,
              li: ({children}) => <li className="text-gray-700">{children}</li>,
              blockquote: ({children}) => <blockquote className="border-l-4 border-blue-200 pl-4 my-4 text-gray-600 italic">{children}</blockquote>,
              code: ({children, className}) => {
                const match = /language-(\w+)/.exec(className || '')
                return match ? (
                  <code className={`${className} text-sm`}>{children}</code>
                ) : (
                  <code className="bg-gray-100 text-pink-600 px-1 py-0.5 rounded text-sm font-mono">{children}</code>
                )
              },
              pre: ({children}) => <pre className="bg-gray-50 border border-gray-200 rounded-lg p-4 overflow-x-auto mb-4">{children}</pre>,
              strong: ({children}) => <strong className="font-semibold text-gray-900">{children}</strong>,
              em: ({children}) => <em className="italic text-gray-700">{children}</em>,
              a: ({children, href}) => <a href={href} className="text-blue-600 hover:text-blue-800 underline">{children}</a>,
              table: ({children}) => <table className="w-full border-collapse border border-gray-300 mb-4">{children}</table>,
              th: ({children}) => <th className="border border-gray-300 px-4 py-2 bg-gray-50 font-semibold text-left">{children}</th>,
              td: ({children}) => <td className="border border-gray-300 px-4 py-2">{children}</td>,
            }}
          >
            {content}
          </ReactMarkdown>
        </div>
      )}
    </div>
  )
}