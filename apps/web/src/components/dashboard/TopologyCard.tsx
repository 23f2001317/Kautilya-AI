// apps/web/src/components/dashboard/TopologyCard.tsx
'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Plus, FilterX, Activity, Server, Database, LayoutTemplate, Layers } from 'lucide-react';
import type { TopologyData, TopologyNode } from '../../types/topology';

interface TopologyCardProps {
  topology: TopologyData | null;
  selectedService: string | null;
  onSelectService: (serviceName: string | null) => void;
  onAddNode: (node: { name: string; node_type: string; tier: string; connect_to?: string }) => Promise<void>;
}

export function TopologyCard({
  topology,
  selectedService,
  onSelectService,
  onAddNode,
}: TopologyCardProps) {
  const [showAddForm, setShowAddForm] = useState(false);
  const [newNodeName, setNewNodeName] = useState('');
  const [connectTo, setConnectTo] = useState('');
  const [nodeType, setNodeType] = useState('service');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const nodes = topology?.nodes || [];
  const edges = topology?.edges || [];

  const nodeCount = nodes.length;
  const radius = 160;
  const centerX = 280;
  const centerY = 190;

  const positionedNodes = nodes.map((node, i) => {
    const angle = (i / Math.max(nodeCount, 1)) * 2 * Math.PI - Math.PI / 2;
    const x = centerX + radius * Math.cos(angle);
    const y = centerY + radius * Math.sin(angle) * 0.78;
    return { ...node, x, y };
  });

  const nodePosMap = new Map(positionedNodes.map((n) => [n.name, n]));

  const handleAddSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newNodeName.trim()) return;
    setIsSubmitting(true);
    try {
      await onAddNode({
        name: newNodeName.trim(),
        node_type: nodeType,
        tier: 'backend',
        connect_to: connectTo || undefined,
      });
      setNewNodeName('');
      setShowAddForm(false);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div
      className="glass-panel"
      style={{
        padding: '24px 28px',
        display: 'flex',
        flexDirection: 'column',
        gap: '18px',
        position: 'relative',
      }}
    >
      {/* Title Bar */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: '12px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <h2
            style={{
              fontSize: '0.95rem',
              fontWeight: 600,
              color: 'var(--text-primary)',
            }}
          >
            Topology Map
          </h2>
          <span
            className="badge"
            style={{
              fontSize: '0.7rem',
              padding: '1px 8px',
            }}
          >
            {nodes.length} nodes · {edges.length} edges
          </span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          {selectedService && (
            <motion.button
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              type="button"
              onClick={() => onSelectService(null)}
              className="btn btn-outline"
              style={{ padding: '4px 10px', fontSize: '0.74rem', display: 'flex', alignItems: 'center', gap: '4px' }}
            >
              <FilterX size={12} />
              Reset Filter
            </motion.button>
          )}
          <button
            type="button"
            onClick={() => setShowAddForm(!showAddForm)}
            className="btn btn-outline"
            style={{ padding: '4px 12px', fontSize: '0.74rem', display: 'flex', alignItems: 'center', gap: '4px' }}
          >
            <Plus size={12} style={{ transform: showAddForm ? 'rotate(45deg)' : 'rotate(0deg)', transition: 'transform 0.2s' }} />
            {showAddForm ? 'Close' : 'Add Node'}
          </button>
        </div>
      </div>

      {/* Progressive Disclosure: Add Node Form */}
      <AnimatePresence>
        {showAddForm && (
          <motion.form
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            onSubmit={handleAddSubmit}
            style={{
              padding: '16px',
              background: 'var(--bg-subtle)',
              border: '1px solid var(--border-subtle)',
              borderRadius: '10px',
              display: 'flex',
              flexWrap: 'wrap',
              gap: '10px',
              alignItems: 'center',
              overflow: 'hidden',
            }}
          >
          <input
            type="text"
            placeholder="Service name (e.g. raphael-ai)"
            value={newNodeName}
            onChange={(e) => setNewNodeName(e.target.value)}
            style={{
              flex: '1 1 180px',
              padding: '6px 12px',
              background: '#07080c',
              border: '1px solid var(--border-subtle)',
              borderRadius: '6px',
              color: '#fff',
              fontSize: '0.78rem',
              outline: 'none',
            }}
          />
          <select
            value={nodeType}
            onChange={(e) => setNodeType(e.target.value)}
            style={{
              padding: '6px 10px',
              background: '#07080c',
              border: '1px solid var(--border-subtle)',
              borderRadius: '6px',
              color: 'var(--text-secondary)',
              fontSize: '0.78rem',
              outline: 'none',
            }}
          >
            <option value="service">Service</option>
            <option value="database">Database</option>
            <option value="cache">Cache</option>
            <option value="frontend">Frontend</option>
          </select>
          <select
            value={connectTo}
            onChange={(e) => setConnectTo(e.target.value)}
            style={{
              padding: '6px 10px',
              background: '#07080c',
              border: '1px solid var(--border-subtle)',
              borderRadius: '6px',
              color: 'var(--text-secondary)',
              fontSize: '0.78rem',
              outline: 'none',
            }}
          >
            <option value="">Connect to...</option>
            {nodes.map((n) => (
              <option key={n.id} value={n.name}>
                {n.name}
              </option>
            ))}
          </select>
          <button
            type="submit"
            disabled={isSubmitting || !newNodeName.trim()}
            className="btn btn-primary"
            style={{ padding: '6px 14px', fontSize: '0.78rem' }}
          >
            {isSubmitting ? 'Adding...' : 'Save'}
          </button>
          </motion.form>
        )}
      </AnimatePresence>

      {/* Clean SVG Canvas */}
      <div
        style={{
          width: '100%',
          height: '380px',
          background: 'var(--bg-subtle)',
          borderRadius: '10px',
          border: '1px solid var(--border-subtle)',
          position: 'relative',
          overflow: 'hidden',
        }}
      >
        <svg
          viewBox="0 0 560 380"
          style={{ width: '100%', height: '100%', display: 'block' }}
        >
          {/* Edges */}
          {edges.map((edge, idx) => {
            const src = nodePosMap.get(edge.source);
            const tgt = nodePosMap.get(edge.target);
            if (!src || !tgt) return null;

            const isHighlighted =
              selectedService &&
              (src.name === selectedService || tgt.name === selectedService);

            return (
              <motion.line
                key={edge.id}
                initial={{ pathLength: 0, opacity: 0 }}
                animate={{ pathLength: 1, opacity: 1 }}
                transition={{ duration: 0.8, delay: idx * 0.05 }}
                x1={src.x}
                y1={src.y}
                x2={tgt.x}
                y2={tgt.y}
                stroke={isHighlighted ? 'var(--color-primary)' : 'rgba(255, 255, 255, 0.08)'}
                strokeWidth={isHighlighted ? 1.5 : 1}
                strokeDasharray={isHighlighted ? 'none' : '4, 4'}
              />
            );
          })}

          {/* Nodes */}
          {positionedNodes.map((node, idx) => {
            const isSelected = selectedService === node.name;

            return (
              <motion.g
                key={node.id}
                initial={{ opacity: 0, scale: 0, x: node.x, y: node.y }}
                animate={{ opacity: 1, scale: 1, x: node.x, y: node.y }}
                transition={{ type: "spring", stiffness: 200, damping: 20, delay: idx * 0.1 }}
                onClick={() =>
                  onSelectService(selectedService === node.name ? null : node.name)
                }
                style={{ cursor: 'pointer' }}
                whileHover={{ scale: 1.1 }}
              >
                {/* Clean node circle */}
                <motion.circle
                  r={isSelected ? 22 : 18}
                  fill={isSelected ? '#0c1624' : '#0a0d14'}
                  stroke={isSelected ? 'var(--color-primary)' : 'rgba(255, 255, 255, 0.12)'}
                  strokeWidth={isSelected ? 2 : 1}
                  animate={{
                    boxShadow: isSelected ? '0 0 15px rgba(0,255,255,0.4)' : 'none',
                  }}
                />

                {/* Node center status dot */}
                <motion.circle
                  r={3}
                  fill={isSelected ? 'var(--color-primary)' : 'rgba(255, 255, 255, 0.4)'}
                />

                {/* Node Label */}
                <text
                  y={32}
                  textAnchor="middle"
                  fill={isSelected ? 'var(--color-primary)' : 'var(--text-secondary)'}
                  fontSize={10}
                  fontWeight={isSelected ? 600 : 400}
                  fontFamily="var(--font-sans)"
                  letterSpacing="-0.01em"
                >
                  {node.name}
                </text>
              </motion.g>
            );
          })}
        </svg>
      </div>
    </div>
  );
}
