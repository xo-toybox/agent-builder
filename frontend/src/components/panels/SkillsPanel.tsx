import { Panel } from '../layout/Panel';

export function SkillsPanel() {
  return (
    <Panel
      title="Skills"
      accent="blue"
      action={
        <button className="text-gray-400 hover:text-white text-xl leading-none">
          +
        </button>
      }
    >
      <div className="text-center py-4">
        <p className="text-gray-500 text-sm">No skills configured</p>
        <p className="text-gray-600 text-xs mt-1">Coming in v0.0.2</p>
      </div>
    </Panel>
  );
}
