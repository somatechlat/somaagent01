# Canvas Integration Documentation for SomaAgent 01

## Overview
The **Dynamic Canvas Selection** system enables SomaAgent 01 to render different canvas implementations (open‑canvas, Fabric.js, Konva, Rough.js, PixiJS) at runtime based on the current application’s needs. It provides a single entry point (`CanvasFactory`), lazy‑loading of heavy libraries, a unified prop contract, and a React Context (`CanvasContext`) for global canvas‑type state.

## Installation
```bash
cd /a0/webui
npm install open-canvas fabric react-fabricjs konva react-konva rough react-rough @inlet/react-pixi axios
```
All libraries are MIT/LGPL‑3.0 licensed.

## File Structure
```
a0/webui/
├─ src/
│  ├─ components/
│  │  └─ CanvasFactory/
│  │      ├─ CanvasFactory.jsx          # Main factory component
│  │      ├─ config.js                  # Registry of lazy imports
│  │      ├─ CanvasContext.jsx          # React context provider
│  │      ├─ Toolbar.jsx                # UI for manual canvas switching
│  │      └─ wrappers/
│  │          ├─ OpenCanvasWrapper.jsx   # Wrapper for open‑canvas
│  │          ├─ FabricWrapper.jsx       # Wrapper for Fabric.js
│  │          ├─ KonvaWrapper.jsx        # Wrapper for react‑konva
│  │          ├─ RoughWrapper.jsx        # Wrapper for react‑rough
│  │          └─ PixiWrapper.jsx         # Wrapper for @inlet/react-pixi
│  └─ pages/
│      └─ canvas.jsx                # Example page using CanvasFactory
├─ public/                               # static assets (unchanged)
├─ styles/globals.css                    # add CSS variables if not present
└─ README.md                             # add a link to this documentation
```

## Core Components
### `config.js`
```js
export const canvasMap = {
  open: () => import('./wrappers/OpenCanvasWrapper'),
  fabric: () => import('./wrappers/FabricWrapper'),
  konva: () => import('./wrappers/KonvaWrapper'),
  rough: () => import('./wrappers/RoughWrapper'),
  pixi: () => import('./wrappers/PixiWrapper'),
};
```
### `CanvasContext.jsx`
```jsx
import { createContext, useContext, useState } from 'react';
const CanvasContext = createContext({ canvasType: 'open', setCanvasType: () => {} });
export const CanvasProvider = ({ children, defaultType = 'open' }) => {
  const [canvasType, setCanvasType] = useState(defaultType);
  return <CanvasContext.Provider value={{ canvasType, setCanvasType }}>{children}</CanvasContext.Provider>;
};
export const useCanvas = () => useContext(CanvasContext);
```
### `CanvasFactory.jsx`
```jsx
import dynamic from 'next/dynamic';
import { canvasMap } from './config';
import { useCanvas } from './CanvasContext';
export default function CanvasFactory({ canvasProps }) {
  const { canvasType } = useCanvas();
  const LazyComponent = dynamic(canvasMap[canvasType] || canvasMap['open'], { ssr: false, loading: () => <div>Loading canvas…</div> });
  return <LazyComponent {...canvasProps} />;
}
```
### `Toolbar.jsx`
```jsx
import { useCanvas } from './CanvasContext';
import styles from './Toolbar.module.css';
export default function Toolbar() {
  const { setCanvasType } = useCanvas();
  return (
    <div className={styles.toolbar}>
      <button onClick={() => setCanvasType('open')}>Simple Chart</button>
      <button onClick={() => setCanvasType('fabric')}>Annotator</button>
      <button onClick={() => setCanvasType('konva')}>Dashboard</button>
      <button onClick={() => setCanvasType('rough')}>Sketchy</button>
      <button onClick={() => setCanvasType('pixi')}>GPU‑Viz</button>
    </div>
  );
}
```
### Wrapper Templates (Unified API)
All wrappers accept the same props:
- `data` – dataset to visualise
- `onZoom`, `onPan`, `onSelect`, `onEdit` – callbacks
- `theme` – `'light' | 'dark'`
- any additional library‑specific props are passed through.

#### OpenCanvasWrapper.jsx
```jsx
import OpenCanvas from 'open-canvas';
export default function OpenCanvasWrapper({ data, onZoom, onPan, theme, ...rest }) {
  const bg = theme === 'dark' ? 'var(--bg-dark)' : 'var(--bg-light)';
  return <OpenCanvas data={data} onZoom={onZoom} onPan={onPan} style={{ background: bg, width: '100%', height: '100%' }} {...rest} />;
}
```
#### FabricWrapper.jsx
```jsx
import { FabricJSCanvas, useFabricJSEditor } from 'react-fabricjs';
import { useEffect } from 'react';
export default function FabricWrapper({ data, onSelect, theme, ...rest }) {
  const { editor, onReady } = useFabricJSEditor();
  useEffect(() => { if (data && editor) editor.loadFromJSON(data); }, [data, editor]);
  const handleSelection = () => { const active = editor?.canvas?.getActiveObject(); if (active && onSelect) onSelect(active.id); };
  return <FabricJSCanvas onReady={onReady} onMouseUp={handleSelection} style={{ background: theme === 'dark' ? 'var(--bg-dark)' : 'var(--bg-light)', width: '100%', height: '100%' }} {...rest} />;
}
```
#### KonvaWrapper.jsx
```jsx
import { Stage, Layer, Rect, Text } from 'react-konva';
import { useState } from 'react';
export default function KonvaWrapper({ data, onSelect, theme, ...rest }) {
  const [scale, setScale] = useState(1);
  const [pos, setPos] = useState({ x: 0, y: 0 });
  const handleWheel = (e) => {
    e.evt.preventDefault();
    const scaleBy = 1.05;
    const oldScale = scale;
    const mousePointTo = { x: e.evt.offsetX / oldScale - pos.x / oldScale, y: e.evt.offsetY / oldScale - pos.y / oldScale };
    const newScale = e.evt.deltaY > 0 ? oldScale / scaleBy : oldScale * scaleBy;
    setScale(newScale);
    setPos({ x: -(mousePointTo.x - e.evt.offsetX / newScale) * newScale, y: -(mousePointTo.y - e.evt.offsetY / newScale) * newScale });
  };
  const bg = theme === 'dark' ? 'var(--bg-dark)' : 'var(--bg-light)';
  return (
    <Stage width={window.innerWidth} height={window.innerHeight} scaleX={scale} scaleY={scale} x={pos.x} y={pos.y} onWheel={handleWheel} style={{ background: bg }} {...rest}>
      <Layer>
        {Array.isArray(data) && data.map(item => (
          <Rect key={item.id} id={item.id} x={item.x} y={item.y} width={item.width} height={item.height} fill={item.fill || '#00D2FF'} draggable onClick={() => onSelect && onSelect(item.id)} />
        ))}
        <Text text="Konva Canvas" x={10} y={10} fill="black" />
      </Layer>
    </Stage>
  );
}
```
#### RoughWrapper.jsx
```jsx
import { RoughSVG } from 'react-rough';
export default function RoughWrapper({ data, theme, ...rest }) {
  const bg = theme === 'dark' ? 'var(--bg-dark)' : 'var(--bg-light)';
  return (
    <svg width="100%" height="100%" style={{ background: bg }} {...rest}>
      <RoughSVG>
        {Array.isArray(data) && data.map((shape, i) => {
          if (shape.type === 'rect') return <rect key={i} x={shape.x} y={shape.y} width={shape.width} height={shape.height} fill={shape.fill} />;
          if (shape.type === 'circle') return <circle key={i} cx={shape.cx} cy={shape.cy} r={shape.r} fill={shape.fill} />;
          return null;
        })}
      </RoughSVG>
    </svg>
  );
}
```
#### PixiWrapper.jsx
```jsx
import { Stage, Sprite, Container } from '@inlet/react-pixi';
export default function PixiWrapper({ data, theme, ...rest }) {
  const bg = theme === 'dark' ? 0x111111 : 0xffffff;
  return (
    <Stage width={window.innerWidth} height={window.innerHeight} options={{ backgroundColor: bg }} {...rest}>
      <Container>
        {Array.isArray(data) && data.map((item, i) => (
          <Sprite key={i} image={item.image} x={item.x} y={item.y} width={item.width} height={item.height} interactive pointerdown={item.onClick} />
        ))}
      </Container>
    </Stage>
  );
}
```

## Example Page (`src/pages/canvas.jsx`)
```jsx
import { CanvasProvider } from '@/components/CanvasFactory/CanvasContext';
import CanvasFactory from '@/components/CanvasFactory/CanvasFactory';
import Toolbar from '@/components/CanvasFactory/Toolbar';
import { useKPIData } from '@/hooks/useKPIData';
import { useTheme } from '@/hooks/useTheme';

export default function CanvasPage() {
  const data = useKPIData();
  const { theme } = useTheme();
  const canvasProps = { data, theme, onZoom: s => console.log('zoom', s), onPan: (dx, dy) => console.log('pan', dx, dy), onSelect: id => console.log('selected', id) };
  return (
    <CanvasProvider defaultType="open">
      <div style={{ padding: '1rem' }}>
        <Toolbar />
        <div style={{ width: '100%', height: '80vh', border: '1px solid var(--border-color)' }}>
          <CanvasFactory canvasProps={canvasProps} />
        </div>
      </div>
    </CanvasProvider>
  );
}
```

## CSS Variables (add to `styles/globals.css` if missing)
```css
:root {
  --bg-light: #ffffff;
  --bg-dark: #1e1e1e;
  --button-bg: #0070f3;
  --button-bg-hover: #0059c1;
  --button-fg: #ffffff;
  --border-color: #eaeaea;
}
[data-theme='dark'] {
  --bg-light: var(--bg-dark);
  --button-bg: #0059c1;
  --button-bg-hover: #004099;
}
```

## Performance Tips
- **Lazy‑load** each canvas library via `next/dynamic` (already done). 
- **SSR disabled** for canvas components to avoid server‑side rendering errors. 
- **Clean‑up** event listeners in each wrapper’s `useEffect` return function. 
- **Pass minimal data** – only the subset required for the visualisation.

## Future Extensions
- Collaborative editing with **Yjs**.
- 3‑D visualisation via **react‑three‑fiber** (add a `three` entry to `config.js`).
- Plugin registration API (`registerCanvas(name, loader)`).
- Accessibility improvements (ARIA, keyboard shortcuts).

---
*Documentation added to `/a0/webui/docs/CanvasIntegration.md`.*
