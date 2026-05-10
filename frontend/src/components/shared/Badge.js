import React from 'react';

const Badge = ({ type, label }) => {
  // Types: "significant" | "not-significant" | "upregulated" | "downregulated" | "unchanged" | "mutated" | "not-mutated"
  return (
    <span className={`badge badge-${type}`}>
      {label}
    </span>
  );
};

export default Badge;
