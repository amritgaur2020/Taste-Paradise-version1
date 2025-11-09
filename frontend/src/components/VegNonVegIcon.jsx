import React from 'react';

const VegNonVegIcon = ({ type = 'veg', size = '14px' }) => {
  const getColor = () => {
    switch(type.toLowerCase()) {
      case 'non-veg':
      case 'nonveg':
        return '#D32F2F';
      case 'veg':
        return '#4CAF50';
      default:
        return '#9E9E9E';
    }
  };

  const iconStyle = {
    width: size,
    height: size,
    border: `2px solid ${getColor()}`,
    borderRadius: '2px',
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: '6px',
    flexShrink: 0
  };

  const dotStyle = {
    width: '6px',
    height: '6px',
    borderRadius: '50%',
    backgroundColor: getColor()
  };

  return (
    <span style={iconStyle}>
      <span style={dotStyle}></span>
    </span>
  );
};

export default VegNonVegIcon;
