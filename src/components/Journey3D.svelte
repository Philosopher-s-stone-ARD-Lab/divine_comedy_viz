<script>
  import { onMount } from 'svelte';
  import * as THREE from 'three';
  import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
  import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
  import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
  import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
  import { CSS2DRenderer, CSS2DObject } from 'three/addons/renderers/CSS2DRenderer.js';
  import * as TWEEN from '@tweenjs/tween.js';

  import { ensureTooltip, showTooltip, hideTooltip, journeyColorScale } from '../utils/d3Helpers.js';
  import {
    REALM_3D_CONFIG,
    mapCantoTo3D,
    createCantoNodes,
    createJourneyPath,
    createRealmBackdrop,
    createParticles,
    updateParticles,
    createHighlightSphere,
    disposeScene,
  } from '../utils/threeHelpers.js';

  let { journeyData = [], mainData = null, onCantoSelect = () => {} } = $props();

  let outerContainer;
  let canvasContainer;
  let width = $state(900);
  let height = $state(600);
  let activeRealm = $state('All');
  let isFullscreen = $state(false);

  function toggleFullscreen() {
    if (!outerContainer) return;
    if (!document.fullscreenElement) {
      outerContainer.requestFullscreen().catch(() => {});
    } else {
      document.exitFullscreen().catch(() => {});
    }
  }

  // Sync state when fullscreen is exited via Escape or browser chrome
  function onFullscreenChange() {
    isFullscreen = !!document.fullscreenElement;
  }

  // Persistent refs across effects (not reactive)
  let sceneRef = null;
  let cantoMeshes = [];
  let particleSystems = [];
  let realmGroups = {};
  let highlightMesh = null;
  let hoveredCanto = null;

  onMount(() => {
    if (!journeyData.length || !canvasContainer) return;

    // ── Renderer ──────────────────────────────────────────────
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setSize(width, height);
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.2;
    renderer.domElement.style.borderRadius = '8px';
    canvasContainer.appendChild(renderer.domElement);

    // ── CSS2D Label Renderer ──────────────────────────────────
    const labelRenderer = new CSS2DRenderer();
    labelRenderer.setSize(width, height);
    labelRenderer.domElement.style.position = 'absolute';
    labelRenderer.domElement.style.top = '0';
    labelRenderer.domElement.style.left = '0';
    labelRenderer.domElement.style.pointerEvents = 'none';
    canvasContainer.appendChild(labelRenderer.domElement);

    // ── Scene ─────────────────────────────────────────────────
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x0a0a0f);
    scene.fog = new THREE.FogExp2(0x0a0a0f, 0.012);

    // ── Camera ────────────────────────────────────────────────
    const camera = new THREE.PerspectiveCamera(60, width / height, 0.1, 1000);
    camera.position.set(8, 4, 8);
    camera.lookAt(0, 1, 0);

    // ── Controls ──────────────────────────────────────────────
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controls.minDistance = 3;
    controls.maxDistance = 30;
    controls.autoRotate = true;
    controls.autoRotateSpeed = 0.3;
    controls.target.set(0, 1.5, 0);
    controls.update();

    // ── Lighting ──────────────────────────────────────────────
    const ambientLight = new THREE.AmbientLight(0x404060, 0.5);
    scene.add(ambientLight);

    const dirLight = new THREE.DirectionalLight(0xffffff, 0.6);
    dirLight.position.set(5, 10, 5);
    scene.add(dirLight);

    // Warm point light at Paradiso apex
    const paradisoConfig = REALM_3D_CONFIG.Paradiso;
    const pointLight = new THREE.PointLight(0xFFD700, 0.8, 20);
    pointLight.position.set(0, (paradisoConfig.yMin + paradisoConfig.yMax) / 2, 0);
    scene.add(pointLight);

    // Dim red point light at Inferno bottom
    const infernoConfig = REALM_3D_CONFIG.Inferno;
    const infernoLight = new THREE.PointLight(0xFF4500, 0.4, 15);
    infernoLight.position.set(0, infernoConfig.yMin, 0);
    scene.add(infernoLight);

    // ── Build Scene Content ───────────────────────────────────

    // Journey path tube
    const pathMesh = createJourneyPath(journeyData);
    scene.add(pathMesh);

    // Canto nodes per realm
    const realmNames = ['Inferno', 'Purgatorio', 'Paradiso'];
    cantoMeshes = [];

    realmNames.forEach(realmName => {
      const group = new THREE.Group();
      group.name = realmName;
      realmGroups[realmName] = group;

      // Filter cantos for this realm
      const realmCantos = journeyData.filter(c => c.realm === realmName);

      // Canto nodes
      const nodesMesh = createCantoNodes(realmCantos, journeyData);
      group.add(nodesMesh);
      cantoMeshes.push(nodesMesh);

      // Realm backdrop
      const backdrop = createRealmBackdrop(realmName);
      group.add(backdrop);

      // Particles
      const particles = createParticles(realmName);
      group.add(particles);
      particleSystems.push(particles);

      scene.add(group);
    });

    // Highlight sphere (initially invisible)
    highlightMesh = createHighlightSphere();
    scene.add(highlightMesh);

    // ── Realm Labels (CSS2D) ──────────────────────────────────
    realmNames.forEach(realmName => {
      const config = REALM_3D_CONFIG[realmName];
      const yCenter = (config.yMin + config.yMax) / 2;

      const labelDiv = document.createElement('div');
      labelDiv.textContent = realmName;
      labelDiv.style.fontFamily = "'EB Garamond', Georgia, serif";
      labelDiv.style.fontSize = '14px';
      labelDiv.style.fontWeight = '600';
      labelDiv.style.color = '#' + config.color.toString(16).padStart(6, '0');
      labelDiv.style.opacity = '0.7';
      labelDiv.style.textShadow = '0 0 8px rgba(0,0,0,0.8)';
      labelDiv.style.letterSpacing = '2px';

      const label = new CSS2DObject(labelDiv);
      label.position.set(5, yCenter, 0);
      scene.add(label);
    });

    // ── Post-Processing ───────────────────────────────────────
    const composer = new EffectComposer(renderer);
    composer.addPass(new RenderPass(scene, camera));

    const bloomPass = new UnrealBloomPass(
      new THREE.Vector2(width, height),
      0.3,   // strength
      0.4,   // radius
      0.85   // threshold
    );
    composer.addPass(bloomPass);

    // ── Raycaster ─────────────────────────────────────────────
    const raycaster = new THREE.Raycaster();
    const mouse = new THREE.Vector2();
    const tooltip = ensureTooltip();
    const colorScale = journeyColorScale();

    function onPointerMove(event) {
      const rect = renderer.domElement.getBoundingClientRect();
      mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
      mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

      raycaster.setFromCamera(mouse, camera);
      const intersects = raycaster.intersectObjects(cantoMeshes, false);

      if (intersects.length > 0) {
        const hit = intersects[0];
        const instanceId = hit.instanceId;
        const mesh = hit.object;
        const canto = mesh.userData.cantos[instanceId];

        if (canto) {
          hoveredCanto = canto;
          renderer.domElement.style.cursor = 'pointer';
          controls.autoRotate = false;

          // Position highlight sphere
          const pos = mapCantoTo3D(canto, instanceId);
          const wordExtent = [
            Math.min(...journeyData.map(d => d.word_count)),
            Math.max(...journeyData.map(d => d.word_count))
          ];
          const sizeT = (canto.word_count - wordExtent[0]) / (wordExtent[1] - wordExtent[0]);
          const nodeRadius = 0.07 + sizeT * 0.15;
          highlightMesh.position.copy(pos);
          highlightMesh.scale.set(nodeRadius * 1.8, nodeRadius * 1.8, nodeRadius * 1.8);
          highlightMesh.visible = true;

          // Tooltip
          const allCantos = mainData?.realms?.flatMap(r => r.cantos) || [];
          const cantoDetail = allCantos.find(c => c.global_number === canto.global_canto);
          const chars = cantoDetail?.characters?.slice(0, 3).map(c => c.name).join(', ') || '';
          const themes = cantoDetail?.key_themes?.slice(0, 3).map(t => t.theme).join(', ') || '';

          showTooltip(tooltip, `
            <div style="font-weight:bold;color:${colorScale(canto.global_canto)};font-size:14px;">
              ${canto.realm}: ${canto.title}
            </div>
            <div style="margin-top:4px;">
              <span style="color:#999">Location:</span> ${canto.location}<br/>
              <span style="color:#999">Words:</span> ${canto.word_count}<br/>
              <span style="color:#999">Sentiment:</span> ${canto.sentiment.toFixed(3)}<br/>
              <span style="color:#999">Theme:</span> ${canto.dominant_theme}<br/>
              ${chars ? `<span style="color:#999">Characters:</span> ${chars}<br/>` : ''}
              ${themes ? `<span style="color:#999">Themes:</span> ${themes}` : ''}
            </div>
          `, event);
        }
      } else {
        if (hoveredCanto) {
          hoveredCanto = null;
          renderer.domElement.style.cursor = 'grab';
          highlightMesh.visible = false;
          hideTooltip(tooltip);
          controls.autoRotate = true;
        }
      }
    }

    function onClick() {
      if (hoveredCanto) {
        onCantoSelect(hoveredCanto.global_canto);
      }
    }

    renderer.domElement.addEventListener('pointermove', onPointerMove);
    renderer.domElement.addEventListener('click', onClick);

    // ── Animation Loop ────────────────────────────────────────
    let animationId;
    function animate(time) {
      animationId = requestAnimationFrame(animate);
      controls.update();
      TWEEN.update(time);
      updateParticles(particleSystems, time);
      composer.render();
      labelRenderer.render(scene, camera);
    }
    animationId = requestAnimationFrame(animate);

    // ── Resize Observer ───────────────────────────────────────
    const ro = new ResizeObserver(entries => {
      for (const entry of entries) {
        width = entry.contentRect.width;
        height = Math.max(500, entry.contentRect.height);
      }
    });
    ro.observe(canvasContainer);

    // Store scene ref for $effect
    sceneRef = {
      renderer, labelRenderer, scene, camera, controls,
      composer, bloomPass, ro, animationId,
    };

    // ── Cleanup ───────────────────────────────────────────────
    return () => {
      cancelAnimationFrame(animationId);
      ro.disconnect();
      renderer.domElement.removeEventListener('pointermove', onPointerMove);
      renderer.domElement.removeEventListener('click', onClick);
      controls.dispose();
      composer.dispose();
      disposeScene(scene);
      renderer.dispose();
      if (canvasContainer?.contains(renderer.domElement)) {
        canvasContainer.removeChild(renderer.domElement);
      }
      if (canvasContainer?.contains(labelRenderer.domElement)) {
        canvasContainer.removeChild(labelRenderer.domElement);
      }
      sceneRef = null;
      cantoMeshes = [];
      particleSystems = [];
      realmGroups = {};
    };
  });

  // ── Reactive: Resize ────────────────────────────────────────
  $effect(() => {
    if (sceneRef && width && height) {
      const { renderer, labelRenderer, camera, composer, bloomPass } = sceneRef;
      renderer.setSize(width, height);
      labelRenderer.setSize(width, height);
      camera.aspect = width / height;
      camera.updateProjectionMatrix();
      composer.setSize(width, height);
      bloomPass.resolution.set(width, height);
    }
  });

  // ── Reactive: Realm Filter ──────────────────────────────────
  $effect(() => {
    if (!sceneRef || !realmGroups.Inferno) return;

    const realms = ['Inferno', 'Purgatorio', 'Paradiso'];

    if (activeRealm === 'All') {
      // Show all realms at full opacity
      realms.forEach(r => {
        realmGroups[r].visible = true;
        realmGroups[r].traverse(child => {
          if (child.material && child.material.opacity !== undefined) {
            // Restore original opacity
          }
        });
      });
      // Reset camera target to center
      new TWEEN.Tween(sceneRef.controls.target)
        .to({ x: 0, y: 1.5, z: 0 }, 800)
        .easing(TWEEN.Easing.Quadratic.InOut)
        .start();
    } else {
      const config = REALM_3D_CONFIG[activeRealm];
      const yCenter = (config.yMin + config.yMax) / 2;

      // Dim non-selected realms
      realms.forEach(r => {
        realmGroups[r].visible = true;
        realmGroups[r].traverse(child => {
          if (child.material) {
            if (r === activeRealm) {
              child.material.opacity = child.material.userData?.originalOpacity ?? child.material.opacity;
            } else {
              // Store original opacity on first dim
              if (child.material.userData === undefined) child.material.userData = {};
              if (child.material.userData.originalOpacity === undefined) {
                child.material.userData.originalOpacity = child.material.opacity;
              }
              child.material.opacity = Math.min(child.material.opacity, 0.08);
            }
            child.material.needsUpdate = true;
          }
        });
      });

      // Tween camera to focus on selected realm
      new TWEEN.Tween(sceneRef.controls.target)
        .to({ x: 0, y: yCenter, z: 0 }, 800)
        .easing(TWEEN.Easing.Quadratic.InOut)
        .start();
    }
  });
</script>

<div class="journey3d-container">
  <div class="controls-bar">
    <div class="realm-filter">
      {#each ['All', 'Inferno', 'Purgatorio', 'Paradiso'] as realm}
        <button
          class="filter-btn"
          class:active={activeRealm === realm}
          onclick={() => { activeRealm = realm; }}
        >
          {realm}
        </button>
      {/each}
    </div>
    <div class="hint">Drag to orbit &middot; Scroll to zoom &middot; Click a canto to explore</div>
  </div>
  <div class="canvas-wrapper" bind:this={canvasContainer}></div>
</div>

<style>
  .journey3d-container {
    width: 100%;
    display: flex;
    flex-direction: column;
    gap: 10px;
  }
  .controls-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 8px;
  }
  .realm-filter {
    display: flex;
    gap: 8px;
  }
  .filter-btn {
    background: transparent;
    color: #aaa;
    border: 1px solid #444;
    padding: 4px 14px;
    border-radius: 16px;
    cursor: pointer;
    font-size: 12px;
    font-family: 'EB Garamond', Georgia, serif;
    transition: all 0.2s;
  }
  .filter-btn:hover {
    color: #fff;
    border-color: #888;
  }
  .filter-btn.active {
    color: #fff;
    background: rgba(255,255,255,0.08);
    border-color: #aaa;
  }
  .hint {
    font-size: 11px;
    color: #555;
    font-family: 'EB Garamond', Georgia, serif;
    font-style: italic;
  }
  .canvas-wrapper {
    position: relative;
    width: 100%;
    min-height: 550px;
    height: 65vh;
    border-radius: 8px;
    overflow: hidden;
    background: #0a0a0f;
  }
  .canvas-wrapper :global(canvas) {
    display: block;
    width: 100% !important;
    height: 100% !important;
  }
</style>
