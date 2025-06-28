if [[ "$OSTYPE" == "darwin"* ]]; then
  grep 'OPENAI_API_KEY' .env | head -n 1 | cut -d '=' -f2- | pbcopy
else
  grep 'OPENAI_API_KEY' .env | head -n 1 | cut -d '=' -f2- | clip
fi
