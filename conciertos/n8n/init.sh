#!/bin/sh
# Arranca n8n en background, espera a que esté listo e importa el workflow

n8n start &
N8N_PID=$!

echo "Esperando a que n8n arranque..."
until wget -q -O /dev/null http://localhost:5678/healthz 2>/dev/null; do
  sleep 2
done

echo "n8n listo. Importando workflow..."
n8n import:workflow --input=/workflows/workflow.json

echo "Workflow importado y activo. n8n en marcha."
wait $N8N_PID