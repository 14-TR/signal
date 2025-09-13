import { NextRequest, NextResponse } from 'next/server';

export async function POST(req: NextRequest) {
  const { level, text } = await req.json();

  if (!process.env.OPENAI_API_KEY) {
    return NextResponse.json(
      { error: 'Missing OPENAI_API_KEY environment variable' },
      { status: 500 }
    );
  }

  const prompt = `Provide a ${level.toLowerCase()} level summary of the following text:\n\n${text}`;

  try {
    const response = await fetch('https://api.openai.com/v1/responses', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${process.env.OPENAI_API_KEY}`,
      },
      body: JSON.stringify({
        model: 'gpt-4o-mini',
        input: prompt,
      }),
    });

    if (!response.ok) {
      const err = await response.text();
      return NextResponse.json({ error: err }, { status: 500 });
    }

    const data = await response.json();
    const summary = data.output_text?.trim() ?? '';

    return NextResponse.json({ summary });
  } catch (error: any) {
    return NextResponse.json({ error: error.message }, { status: 500 });
  }
}
