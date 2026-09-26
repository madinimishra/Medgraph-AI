function EventGroup({ title, items }) {
  if (!items || items.length === 0) return null;
  return (
    <div className="journey-event-group">
      <span className="journey-event-group-title">{title}</span>
      <ul>
        {items.map((item) => (
          <li key={item.id}>{item.description}</li>
        ))}
      </ul>
    </div>
  );
}

export default function PatientJourney({ journey }) {
  if (!journey) return null;

  const { patient, encounters } = journey;

  return (
    <div className="patient-journey">
      <div className="journey-patient-header">
        <h3>
          {patient.first_name} {patient.last_name}
        </h3>
        <span className="journey-patient-meta">
          {patient.gender} · born {patient.birthdate} · {patient.race}, {patient.ethnicity}
        </span>
      </div>

      <div className="journey-timeline">
        {encounters.map((encounter) => (
          <div className="journey-item" key={encounter.encounter_id}>
            <div className="journey-item-dot" />
            <div className="journey-item-body">
              <div className="journey-item-header">
                <span className="journey-item-date">{encounter.start_time}</span>
                <span className="journey-item-class">{encounter.encounter_class}</span>
              </div>
              <div className="journey-item-title">{encounter.description}</div>
              <div className="journey-item-provider">
                {encounter.provider_name} · {encounter.organization_name}
              </div>

              <div className="journey-event-groups">
                <EventGroup title="Conditions" items={encounter.conditions} />
                <EventGroup title="Procedures" items={encounter.procedures} />
                <EventGroup title="Medications" items={encounter.medications} />
                <EventGroup title="Observations" items={encounter.observations} />
                <EventGroup title="Allergies" items={encounter.allergies} />
              </div>
            </div>
          </div>
        ))}

        {encounters.length === 0 && (
          <div className="journey-empty">No encounters recorded for this patient.</div>
        )}
      </div>
    </div>
  );
}
