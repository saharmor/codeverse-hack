import React from 'react'

interface StatusCardProps {
  title: string
  status: 'success' | 'error' | 'warning' | 'unknown'
  message: string
  icon?: React.ReactNode
}

const StatusCard: React.FC<StatusCardProps> = ({ title, status, message, icon }) => {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'success':
        return 'bg-green-500'
      case 'error':
        return 'bg-red-500'
      case 'warning':
        return 'bg-yellow-500'
      default:
        return 'bg-gray-500'
    }
  }

  const getStatusTextColor = (status: string) => {
    switch (status) {
      case 'success':
        return 'text-green-700'
      case 'error':
        return 'text-red-700'
      case 'warning':
        return 'text-yellow-700'
      default:
        return 'text-gray-700'
    }
  }

  return (
    <div className="card">
      <h3 className="text-lg font-semibold text-gray-900 mb-2">{title}</h3>
      <div className="flex items-center">
        <div className={`w-3 h-3 ${getStatusColor(status)} rounded-full mr-2`}></div>
        <span className={getStatusTextColor(status)}>{message}</span>
      </div>
      {icon && (
        <div className="mt-3 text-gray-400">
          {icon}
        </div>
      )}
    </div>
  )
}

export default StatusCard 