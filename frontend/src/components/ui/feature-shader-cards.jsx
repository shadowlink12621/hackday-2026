import { lazy, Suspense, useEffect, useRef, useState } from 'react';

const Warp = lazy(() => import('@paper-design/shaders-react').then((module) => ({ default: module.Warp })));

const features = [
  {
    title: 'Gemma-assisted extraction',
    description: 'Pull key names, dates, totals, and line items from submitted claim documents for a faster first review.',
    icon: <path d="M12 2a7 7 0 0 0-4 12.75V18h8v-3.25A7 7 0 0 0 12 2Zm-2 18h4v2h-4v-2Zm4-7.2.8-.55a5 5 0 1 0-5.6 0l.8.55V16h4v-3.2Z" />,
  },
  {
    title: 'Explainable policy checks',
    description: 'Show the rule and reason behind amount, currency, room-rent, and excluded-item flags so reviewers can act on them.',
    icon: <path d="M12 2 3 6v5c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V6l-9-4Zm-1.1 14.2-3.2-3.2 1.42-1.42 1.78 1.78 4.98-4.98 1.42 1.42-6.4 6.4Z" />,
  },
  {
    title: 'Page-linked policy guide',
    description: 'Scan searchable insurance PDFs for coverage highlights, common claim pitfalls, and practical next steps with page references.',
    icon: <path d="M6 2h8l5 5v15H6a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2Zm7 1.5V8h4.5L13 3.5ZM8 12v1.7h8V12H8Zm0 4v1.7h8V16H8Z" />,
  },
  {
    title: 'Duplicate receipt checks',
    description: 'Flag likely repeat submissions for a closer look before they move through the review workflow.',
    icon: <path d="M8 3h11a2 2 0 0 1 2 2v13h-2V5H8V3ZM5 7h11a2 2 0 0 1 2 2v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V9a2 2 0 0 1 2-2Zm0 2v11h11V9H5Z" />,
  },
  {
    title: 'Audit-ready history',
    description: 'Keep processed claims and reviewer decisions together, then export a CSV for follow-up and reporting.',
    icon: <path d="M4 3h16v2H4V3Zm0 4h16v2H4V7Zm0 4h10v2H4v-2Zm0 4h10v2H4v-2Zm13.5-1 4.5 4.5-4.5 4.5-1.4-1.4 2.1-2.1H12v-2h6.2l-2.1-2.1 1.4-1.4Z" />,
  },
  {
    title: 'Human review stays in control',
    description: 'Bring exceptions and supporting details to the surface; ClaimGuard helps teams review instead of silently deciding a claim.',
    icon: <path d="M12 12a5 5 0 1 0 0-10 5 5 0 0 0 0 10Zm0 2c-4.42 0-8 2.24-8 5v3h16v-3c0-2.76-3.58-5-8-5Zm7-8h4v2h-4V6Zm-2.4 1 2.8-2.8 1.4 1.4L18 8.4 16.6 7Z" />,
  },
];

const shaderConfigs = [
  { proportion: 0.34, softness: 0.9, distortion: 0.2, swirl: 0.6, swirlIterations: 8, shape: 'checks', shapeScale: 0.09, colors: ['#003d30', '#00b887', '#00617b', '#00a3b8'] },
  { proportion: 0.42, softness: 0.8, distortion: 0.16, swirl: 0.7, swirlIterations: 9, shape: 'stripes', shapeScale: 0.12, colors: ['#003b35', '#00a887', '#00465c', '#17b8a0'] },
  { proportion: 0.36, softness: 0.95, distortion: 0.18, swirl: 0.65, swirlIterations: 10, shape: 'edge', shapeScale: 0.1, colors: ['#064b3b', '#02b487', '#075273', '#21c2a5'] },
  { proportion: 0.44, softness: 0.85, distortion: 0.19, swirl: 0.72, swirlIterations: 8, shape: 'checks', shapeScale: 0.11, colors: ['#034238', '#00a987', '#064b70', '#00c2a1'] },
  { proportion: 0.32, softness: 0.9, distortion: 0.14, swirl: 0.62, swirlIterations: 11, shape: 'stripes', shapeScale: 0.1, colors: ['#064b36', '#00ab7f', '#063e65', '#10bca4'] },
  { proportion: 0.4, softness: 0.88, distortion: 0.18, swirl: 0.68, swirlIterations: 9, shape: 'edge', shapeScale: 0.12, colors: ['#064737', '#00ad80', '#064c75', '#0bbba4'] },
];

export default function FeatureShaderCards() {
  const sectionRef = useRef(null);
  const [ready, setReady] = useState(false);
  const [reducedMotion, setReducedMotion] = useState(false);

  useEffect(() => {
    const motionQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    const updateMotion = () => setReducedMotion(motionQuery.matches);
    updateMotion();
    motionQuery.addEventListener?.('change', updateMotion);

    const node = sectionRef.current;
    if (!node || !('IntersectionObserver' in window)) {
      setReady(true);
      return () => motionQuery.removeEventListener?.('change', updateMotion);
    }
    const observer = new IntersectionObserver(([entry]) => {
      if (entry.isIntersecting) {
        setReady(true);
        observer.disconnect();
      }
    }, { rootMargin: '180px' });
    observer.observe(node);

    return () => {
      observer.disconnect();
      motionQuery.removeEventListener?.('change', updateMotion);
    };
  }, []);

  return (
    <section className="shader-features" ref={sectionRef} aria-labelledby="shader-features-title">
      <div className="shader-features-heading">
        <div className="eyebrow">CLAIMGUARD CAPABILITIES</div>
        <h2 id="shader-features-title">A clearer path from upload to review</h2>
        <p>Useful claim details up front, with clear reasons when something needs a human look.</p>
      </div>

      <div className="shader-features-grid">
        {features.map((feature, index) => {
          const config = shaderConfigs[index];
          return (
            <article className="shader-feature-card" key={feature.title}>
              {ready && (
                <div className="shader-feature-background" aria-hidden="true">
                  <Suspense fallback={null}>
                    <Warp
                      style={{ width: '100%', height: '100%' }}
                      maxPixelCount={180000}
                      minPixelRatio={1}
                      {...config}
                      scale={1}
                      rotation={0}
                      speed={reducedMotion ? 0 : 0.22}
                    />
                  </Suspense>
                </div>
              )}
              <div className="shader-feature-content">
                <div className="shader-feature-icon" aria-hidden="true">
                  <svg viewBox="0 0 24 24" fill="currentColor">{feature.icon}</svg>
                </div>
                <h3>{feature.title}</h3>
                <p>{feature.description}</p>
              </div>
            </article>
          );
        })}
      </div>
    </section>
  );
}
